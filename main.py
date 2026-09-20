from fastapi import FastAPI,Depends,status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from schema import PostCreate, PostResponse

from datetime import datetime, timezone

import models
from database import get_db, Base, engine


app = FastAPI()

Base.metadata.create_all(bind=engine)



@app.get("/")
def home():
    return {"message": "Welcome to the FastAPI application!"}

@app.get("/api/posts", response_model=list[PostResponse], status_code=status.HTTP_200_OK)
def get_posts(db : Session = Depends(get_db)):
    # return db.query(models.Post).all() # return all the posts in the db
    # or when we want more filters
    result = db.execute(
        select(models.Post)
        .order_by(models.Post.created_date.desc())
    )
    posts = result.scalars().all()
    return posts


# response_model is used to define the structure of the output
# whenever we want to be sure about output format, we use response_model to define the output format
@app.post("/api/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(post: PostCreate, db : Session = Depends(get_db)):
    new_post = models.Post(**post.model_dump()) # whatever comes from the client (post->PostCreate class), and then save in DB with models.Post class and add extra fields
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post
    



@app.get("/api/posts/{post_id}", response_model=PostResponse, status_code=status.HTTP_200_OK)
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.get(models.Post, post_id) # db.get(Model, primary_key)
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
    return post
    
# in put the user has to change all the fields, the not changed fields will return empty and user will get an error
@app.put("/api/posts/{post_id}",response_model=PostResponse)
def update_post_full(post_id:int, post_data: PostCreate, db:Session = Depends(get_db)):
    post = db.get(models.Post, post_id)
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

    db.commit()
    db.refresh(post)
    return post

# in patch the user can change only the fields, that they want and not change fields will return as before
# it cannot use the PostCreate class because the objects are obligatory and not optional
@app.patch("/api/posts/{post_id}",response_model=PostResponse)


@app.delete("/api/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id:int, db: Session = Depends(get_db)):
    post = db.get(models.Post, post_id)
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
    db.delete(post)
    db.commit()
    db.refresh()