'''
Schema.py includes pydantic classes.
Here we define what we expect to recieve from client
and what we reply to a request.
'''
from pydantic import BaseModel, Field, ConfigDict

from datetime import datetime


class PostBase(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=3)
    author: str = Field(min_length=3)

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