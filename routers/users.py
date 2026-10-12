from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func

import models
from database import get_db
from schema import Token, UserCreate, UserPublic,UserPrivate, UserUpdate, PostResponse

from fastapi.security import OAuth2PasswordRequestForm

from auth import(
    CurrentUser,
    hash_password,
    verify_password,
    create_access_token,
    verify_access_token,
    oauth2_schema,

)

from config import settings

router = APIRouter()

@router.post("", response_model=UserPrivate, status_code=status.HTTP_201_CREATED)
async def create_user(new_user: UserCreate, db : Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.User)
        .where(func.lower(models.User.email) == new_user.email.lower()),
    )
    existing_email = result.scalars().first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = models.User(
        full_name=new_user.full_name,
        email=new_user.email.lower(),
        password_hash = hash_password(new_user.password),
    )
        
        

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user



@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Look user by email
    # Oauth2PasswordRequestForm uses "usernam" field, but we treat it as email
    
    result = await db.execute(
        select(models.User)
        .where(func.lower(models.User.email) == form_data.username.lower()),
    )
    user = result.scalars().first()

    # Verify user exists and password is correct
    # We don't reveal which one failed (secuirity)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # create the access token with user id as subject
    access_token = create_access_token(
        data={"sub": str(user.id)},
    )
    return Token(access_token=access_token, token_type="bearer")


# This part is for front end validation 
# make sure the user exist and token is valid before calling th next function with user_id
@router.get("/me", response_model=UserPrivate)
async def get_current_user(current_user: CurrentUser):
    #token: Annotated[str, Depends(oauth2_schema)],
    #db: Annotated[AsyncSession, Depends(get_db)],)

    """Get the current authenticated user."""
    # Now we can delete all codes and use just CurrentUser because they are basically the same
    return current_user
    # user_id = verify_access_token(token)
    # if user_id is None:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Invalid or expired token",
    #         headers={"WWW-Authenticate": "Bearer"},
    #     )

    # # Validate user_id is a valid integer (defense against malformed JWT)
    # # Frontend needs to know who logged in
    # try:
    #     user_id_int = int(user_id)
    # except (TypeError, ValueError):
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Invalid or expired token",
    #         headers={"WWW-Authenticate": "Bearer"},
    #     )

    # # now check the integer user_id is valid and user exists
    # result = await db.execute(
    #     select(models.User)
    #     .where(models.User.id == user_id_int)
    # )
    # user = result.scalars().first()
    # if not user:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="User not found",
    #         headers={"WWW-Authenticate": "Bearer"}
    #     )
    # return user


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

@router.patch("/{user_id}", response_model=UserPrivate)
async def update_user(user_id: int, 
                      user_data:UserUpdate, 
                      current_user: CurrentUser,
                      db: Annotated[AsyncSession, Depends(get_db)],
):

    if user_id != current_user.id:
        raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Not authorized to update this user",
                )
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

    if user_data.email is not None:
        new_email = user_data.email.lower() # same as create_user, emails are stored lowercase
        if new_email != user.email:
            result = await db.execute(
                select(models.User)
                .where(func.lower(models.User.email) == new_email),
            )
            existing_email = result.scalars().first()
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already registered",
                )
        user.email = new_email

    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/{user_id}",status_code=status.HTTP_204_NO_CONTENT)
async def user_delete(user_id: int, current_user:CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
    
    if user_id != current_user.id:
        raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Not authorized to delete this user",
                )

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