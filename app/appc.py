from typing import Optional
from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Depends
from httpx import options
from sqlalchemy.engine import result
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import PostCreate
from app.db import Post, create_db,get_async_session
from contextlib import asynccontextmanager
from sqlalchemy import select
from fastapi.staticfiles import StaticFiles
import os
import shutil

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@asynccontextmanager
async def span(app:FastAPI):
    await create_db()
    yield

app = FastAPI(lifespan=span)


app.mount("/files", StaticFiles(directory=UPLOAD_DIR), name="files")


@app.post("/upload")
async def upload_file(
        file:UploadFile=File(...),
        caption:str=Form(""),
        session:AsyncSession=Depends(get_async_session)
        ):
    filename = file.filename
    if filename is None:
        raise ValueError("filename is required")

    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    post = Post(
            caption=caption,
            url=f"/files/{filename}",
            file_type="photo",
            file_name=filename
            )
    session.add(post)
    await session.commit()
    await session.refresh(post)
    return post



@app.get("/home")
async def get_home(session:AsyncSession=Depends(get_async_session)):
    result = await session.execute(select(Post).order_by(Post.created_at.desc()))
    posts = []
    for row in result.all():
        posts.append(row[0])

    posts_data = []
    for post in posts:
        post_data = {
            "id":str(post.id),
            "caption":post.caption,
            "url":post.url,
            "file_type":post.file_type,
            "file_name":post.file_name,
            "created_at":post.created_at.isoformat()
                }
        posts_data.append(post_data)

    return posts_data



# OLD

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

