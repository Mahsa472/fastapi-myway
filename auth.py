from datetime import UTC, datetime, timedelta

import jwt
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash

from config import settings
# for the second part: authorization
from typing import Annotated

from fastapi import Depends, HTTPException, status

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import models
from database import get_db

# hash password
# verify password
# create access token
# verify access token
SECRET_KEY = settings.secret_key.get_secret_value()
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRES_MINUTES = settings.access_token_expires_minutes

password_hash = PasswordHash.recommended() 
# to hash the password which user write
# We use hash instead of encryption, because hash is not reversible but encryption is

oauth2_schema = OAuth2PasswordBearer(tokenUrl="api/users/token") 
# This part extract the token from authorization header
# This url should match the user login url
# This also activate the Authorize buttom in docs


def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(password=plain_password, hash=hashed_password)


#generate jwt with user data
def create_access_token(data:dict):
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRES_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    return encoded_jwt

#veryfy_token decodes the validate jwt and ensures that authenticity and expiration are correct
def verify_access_token(token:str):
    """Verify a JWT token and return the subject (user id) if valid"""
    try:
        payload = jwt.decode(
            token, 
            SECRET_KEY, 
            algorithms=[ALGORITHM],
            options={"require": ["exp", "sub"]},
            )
        return payload.get("sub")
    except jwt.InvalidTokenError:
        return None



async def get_current_user(
    token: Annotated[str, Depends(oauth2_schema)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get the current authenticated user."""
    user_id = verify_access_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate user_id is a valid integer (defense against malformed JWT)
    # Frontend needs to know who logged in
    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # now check the integer user_id is valid and user exists
    result = await db.execute(
        select(models.User)
        .where(models.User.id == user_id_int)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user

CurrentUser = Annotated[models.User, Depends(get_current_user)]
# model.User is an object of the user
# Depends(get_current_user) is a metadata for the object which is related to get_current_user object