from fastapi import FastAPI,Depends,status, HTTPException
from sqlalchemy.orm import Session

from schema import PostCreate, PostResponse

from datetime import datetime, timezone

import models
from database import get_db, Base, engine


app = FastAPI()

Base.metadata.create_all(bind=engine)



@app.get("/")
async def home():
    return {"message": "Welcome to the FastAPI application!"}

#or
#@app.get("/")
#def home():
#    retrun {"message": "Welcome to the FastAPI application!"}

# response_model is used to define the structure of the output
# whenever we want to be sure about output format, we use response_model to define the output format
@app.post("/api/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(post: PostCreate, db : Session = Depends(get_db)):
    new_post = models.Post(**post.model_dump()) # whatever comes from the client (post->PostCreate class), and then save in DB with models.Post class and add extra fields
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post
    

@app.get("/api/posts", response_model=list[PostResponse], status_code=status.HTTP_200_OK)
async def get_posts(db : Session = Depends(get_db)):
    return db.query(models.Post).all() # return all the posts in the db

@app.get("/api/posts/{post_id}", response_model=PostResponse, status_code=status.HTTP_200_OK)
async def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.get(models.Post, post_id) # db.get(Model, primary_key)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post
    

