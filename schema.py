'''
Schema.py includes pydantic classes.
Here we define what we expect to recieve from client
and what we reply to a request.
'''
from pydantic import BaseModel, Field, ConfigDict, EmailStr

from datetime import datetime



class UserBase(BaseModel):
    full_name: str = Field(min_length=3, max_length=50)
    email: EmailStr = Field(max_length=120)


class UserCreate(UserBase):
    password: str = Field(min_length=8)

# class UserPublic(UserBase): # what returns
#     # what schema returns is a deliberate choice, not every column from models should be there
#     # put posts: list[PostResponse] only creates a loop which is not stable
#     model_config = ConfigDict(from_attributes=True)

#     id: int
#     user_created_at: datetime

# UserPublic inherit from UserBase and that means it has email which we don't want to show
class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    user_created_at: datetime

class UserPrivate(UserPublic):
    email: EmailStr


class UserUpdate(BaseModel): #atm user can only change the email
    email: EmailStr | None = Field(default=None, max_length=120)


class Token(BaseModel):
    access_token: str
    token_type: str


class PostBase(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=3)
    #author: str = Field(min_length=3) # we needed this here befor User class, after user class we don't need it for Update anymore 
    


# here is what we receive from client
class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    content: str | None = Field(default=None, min_length=3)


class PostResponse(PostBase):
    model_config =  ConfigDict(from_attributes=True)

    id: int
    created_date: datetime 
    updated_date: datetime | None
    author: UserPublic
    user_id: int




