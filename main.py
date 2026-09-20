
from fastapi import FastAPI
#from sqlalchemy.orm import Session # insted of AsyncSession for sync 

from routers import posts, users



app = FastAPI()

#Base.metadata.create_all(bind=engine) # we have alembic now

app.include_router(posts.router, prefix="/api/posts", tags=["posts"])
app.include_router(users.router, prefix="/api/users", tags=["users"])

@app.get("/")
def home():
    return {"message": "Welcome to the FastAPI application!"}






