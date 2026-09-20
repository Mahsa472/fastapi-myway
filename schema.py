from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime


class PostBase(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=3)
    author: str = Field(min_length=3)

# here is what we receive from client
class PostCreate(PostBase):
    pass

class PostResponse(PostBase):
    model_config =  ConfigDict(from_attributes=True)

    id: int
    created_date: datetime 