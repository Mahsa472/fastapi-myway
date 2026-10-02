from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from database import get_db
from schema import PostCreate,PostUpdate, PostResponse

from auth import CurrentUser


router = APIRouter() #router instance


@router.get("", response_model=list[PostResponse], status_code=status.HTTP_200_OK)
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
@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(new_post: PostCreate, current_user:CurrentUser, db : Annotated[AsyncSession, Depends(get_db)]):

    #post = models.Post(**new_post.model_dump()) # whatever comes from the client (post->PostCreate class), and then save in DB with models.Post class and add extra fields
    post = models.Post(
        title=new_post.title,
        content=new_post.content,
        user_id=current_user.id,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post, attribute_names=["author"]) # without attribute we get an greenlet error because we return post, but we did not load author form PostRespond
    return post
    



@router.get("/{post_id}", response_model=PostResponse, status_code=status.HTTP_200_OK)
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
@router.put("/{post_id}",response_model=PostResponse)
async def update_post_full(
    post_id:int, 
    post_data: PostCreate,
    current_user: CurrentUser, 
    db : Annotated[AsyncSession, Depends(get_db)]):
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

    if post.user_id != current_user.id:
        raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Not authorized to update this post",
                )
        
    
    post.title = post_data.title
    post.content = post_data.content
    # post.author = post_data.author
    # or one line
    #updated_post = post_data.model_dump()
    #for field, value in updated_post.items():
    #    setattr(post, field, value)

    await db.commit()
    await db.refresh(post, attribute_names=["author"])
    return post

# in patch the user can change only the fields, that they want and not change fields will return as before
# it cannot use the PostCreate class because the objects are obligatory and not optional
@router.patch("/{post_id}",response_model=PostResponse)
async def update_post_partial(
    post_id:int, 
    post_data:PostUpdate, 
    current_user: CurrentUser,
    db : Annotated[AsyncSession, Depends(get_db)]
    ):
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

    if post.user_id != current_user.id:
        raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Not authorized to update this post",
                )

    
    # We check user_id only when it can be set, in update_partial we cannot change user_id so there is no need to check
    updated_post = post_data.model_dump(exclude_unset=True)
    for field, value in updated_post.items():
        setattr(post, field, value)

    await db.commit()
    await db.refresh(post)
    return post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id:int, current_user: CurrentUser, db : Annotated[AsyncSession, Depends(get_db)]):
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
    if post.user_id != current_user.id:
        raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Not authorized to update this post",
                )
    await db.delete(post)
    await db.commit()