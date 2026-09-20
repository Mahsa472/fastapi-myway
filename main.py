from fastapi import FastAPI, HTTPException

from schema import PostCreate, PostResponse

from datetime import datetime, timezone





app = FastAPI()

posts = [{
    "title": "First Post",
    "content": "This is the content of the first post.",
    "author": "John Doe",
    "id": 1,
    "created_date": "2023-01-01T12:00:00"
    },
    {
    "title": "Second Post",
    "content": "This is the content of the second post.",
    "author": "Jane Smith",
    "id": 2,
    "created_date": "2023-01-02T15:30:00"
    }
]




@app.get("/", response_model=list[PostResponse])
async def home():
    return posts

#or
#@app.get("/")
#def home():
#    retrun {"message": "Welcome to the FastAPI application!"}

# response_model is used to define the structure of the output
# whenever we want to be sure about output format, we use response_model to define the output format
@app.post("/api/posts", response_model=PostResponse)
async def create_post(post: PostCreate):
    new_id = max (p["id"] for p in posts) + 1 if posts else 1
    created_date = datetime.now(timezone.utc).isoformat()
    new_post = {
        "title": post.title,
        "content": post.content,
        "author": post.author,
        "id": new_id,
        "created_date": created_date
    }
    posts.append(new_post)

    return new_post  

@app.get("/api/posts", response_model=list[PostResponse])
async def get_posts():
    return posts

@app.get("/api/posts/{post_id}", response_model=PostResponse)
async def get_post(post_id: int):
    for post in posts:
        if post["id"] == post_id:
            return post
    raise HTTPException(status_code=404, detail="Post not found")
    

