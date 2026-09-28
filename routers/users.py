from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func

import models
from database import get_db
from schema import UserCreate, UserPublic, UserUpdate, PostResponse

router = APIRouter()

@router.post("", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
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


@router.get("/{user_id}", response_model=UserPublic)
async def get_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.User)
        .where(models.User.id == user_id)
    )
    user = result.scalars().first()
    if user:
        return user
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found",
    )

@router.get("/{user_id}/posts", response_model=list[PostResponse])
async def get_user_posts(user_id: int, db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
            select(models.User)
            .where(models.User.id == user_id)
        )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
    results = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.user_id == user_id)
    )
    posts = results.scalars().all()
    return posts

@router.patch("/{user_id}", response_model=UserPublic)
async def update_user(user_id: int, user_data:UserUpdate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
                select(models.User)
                .where(models.User.id == user_id),
            )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

    if user_data.email is not None and user_data.email != user.email:
        result = await db.execute(
            select(models.User)
            .where(models.User.email == user_data.email),
        )
        existing_email = result.scalars().first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail="Email already registered",
            )

    if user_data.email is not None:
        user.email = user_data.email

    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/{user_id}",status_code=status.HTTP_204_NO_CONTENT)
async def user_delete(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
            select(models.User)
            .where(models.User.id == user_id),
        )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

    await db.delete(user) # there was a attribute to delete all info of a user check that?? delete orphan
    await db.commit()