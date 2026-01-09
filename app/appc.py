from typing import Optional
from fastapi import FastAPI, HTTPException
from app.schemas import PostCreate
from app.db import Post, create_db

app = FastAPI()


text_posts = {
    1: {"title": "test post", "content": "test content"},
    2: {"title": "post two", "content": "content for post two"},
    3: {"title": "post three", "content": "content for post three"},
    4: {"title": "post four", "content": "content for post four"},
    5: {"title": "post five", "content": "content for post five"},
    6: {"title": "post six", "content": "content for post six"},
    7: {"title": "post seven", "content": "content for post seven"},
    8: {"title": "post eight", "content": "content for post eight"},
}

@app.get("/posts")
def get_all_posts(limit:Optional[int] = None):
    if limit:
        return list(text_posts.values())[:limit]
    return text_posts


@app.get("/posts/{id}")
def get_post(id:int):
    if  id not in text_posts:
        raise HTTPException(status_code=400,detail="post not found")
    return text_posts.get(id)

@app.post("/posts")
def create_post(post:PostCreate) -> dict[str,str]:
    new_post = {"title":post.title, "content":post.content}
    text_posts[max(text_posts.keys()) + 1] = new_post
    return new_post

