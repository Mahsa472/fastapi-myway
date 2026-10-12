'''
Models.py includes sqlalchemy classes.
Sqlalchemy classes define what we want to store in our db
To be able to talk to db we need sqlalchemy

'''


from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime, UTC


# importing some column types
from sqlalchemy import(
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(120),index=True, nullable=False, unique=True)
    user_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default= lambda: datetime.now(UTC))
    posts: Mapped[List["Post"]] = relationship(back_populates="author", cascade="all, delete-orphan") # define a relationship many to one between posts and author, deleting a user also deletes their posts
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True) #primary key will be written automatically by db and index is for faster search
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default= lambda: datetime.now(UTC))
    updated_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True, default=None, onupdate=lambda: datetime.now(UTC) )
    author: Mapped[User] = relationship(back_populates="posts") # define a relationship one to many between author and posts
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
