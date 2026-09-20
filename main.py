from datetime import datetime, timezone
from typing import Annotated

from fastapi import FastAPI,Depends,status, HTTPException
#from sqlalchemy.orm import Session # insted of AsyncSession for sync 
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from schema import PostCreate,PostUpdate, PostResponse, UserCreate, UserPublic, UserUpdate



import models
from database import get_db, Base, engine


app = FastAPI()

#Base.metadata.create_all(bind=engine) # we have alembic now



@app.get("/")
def home():
    return {"message": "Welcome to the FastAPI application!"}

@app.get("/api/posts", response_model=list[PostResponse], status_code=status.HTTP_200_OK)
async def get_posts(db : Annotated[AsyncSession, Depends(get_db)]):
    # return db.query(models.Post).all() # return all the posts in the db
    # or when we want more filters
    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author)) # author is a nested object and it could be that it is not loaded atm of call
        # in sync call it will be loaded in that moment
        # in Async session it cannot make moment call therefore it should be loaded at first on the query
        .order_by(models.Post.created_date.desc())
    )
    posts = result.scalars().all()
    return posts


# response_model is used to define the structure of the output
# whenever we want to be sure about output format, we use response_model to define the output format
@app.post("/api/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(new_post: PostCreate, db : Annotated[AsyncSession, Depends(get_db)]):
    post = models.Post(**new_post.model_dump()) # whatever comes from the client (post->PostCreate class), and then save in DB with models.Post class and add extra fields
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post
    



@app.get("/api/posts/{post_id}", response_model=PostResponse, status_code=status.HTTP_200_OK)
async def get_post(post_id: int, db : Annotated[AsyncSession, Depends(get_db)]):
    #post = await db.get(models.Post, post_id) # db.get(Model, primary_key) we have to change it when we have author nested in PostResponse
    # or with more flexibility
    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.id==post_id)
    )
    post = result.scalars().first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Post not found",
            )
    return post
    
# in put the user has to change all the fields, the not changed fields will return empty and user will get an error
@app.put("/api/posts/{post_id}",response_model=PostResponse)
async def update_post_full(post_id:int, post_data: PostCreate, db : Annotated[AsyncSession, Depends(get_db)]):
    #post = await db.get(models.Post, post_id)
    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.id == post_id)
    )
    post = result.scalars().first()
    if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Post not found",
                )
    # post.title = post_data.title
    # post.content = post_data.content
    # post.author = post_data.author
    # or one line
    updated_post = post_data.model_dump()
    for field, value in updated_post.items():
        setattr(post, field, value)

    await db.commit()
    await db.refresh(post)
    return post

# in patch the user can change only the fields, that they want and not change fields will return as before
# it cannot use the PostCreate class because the objects are obligatory and not optional
@app.patch("/api/posts/{post_id}",response_model=PostResponse)
async def update_post_partial(post_id:int, post_data:PostUpdate, db : Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
            select(models.Post)
            .options(selectinload(models.Post.author))
            .where(models.Post.id == post_id)
        )
    post = result.scalars().first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    updated_post = post_data.model_dump(exclude_unset=True)
    for field, value in updated_post.items():
        setattr(post, field, value)

    await db.commit()
    await db.refresh(post)
    return post


@app.delete("/api/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id:int, db : Annotated[AsyncSession, Depends(get_db)]):
    post = await db.get(models.Post, post_id) # here delete_post returns nothing so we don't need select for author
    # or with more flexibility
    # result = db.execute(
    #     select(models.Post)
    #     .where(models.Post.id==post_id)
    # )
    # post = result.scalars().first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Post not found",
            )
    await db.delete(post)
    await db.commit()




@app.post("/api/users", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def create_user(new_user: UserCreate, db : Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.User)
        .where(func.lower(models.User.email) == new_user.email.lower()),
    )
    existing_email = result.scalars().first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    user = models.User(
        full_name=new_user.full_name,
        email=new_user.email.lower(),
    )
        
        

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user