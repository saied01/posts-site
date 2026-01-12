import uuid
from pathlib import Path as FSPath
from fastapi import FastAPI, HTTPException, File, Path, UploadFile, Form, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import UserCreate, UserRead, UserUpdate
from app.db import Post, create_db,get_async_session, User
from contextlib import asynccontextmanager
from sqlalchemy import select
from fastapi.staticfiles import StaticFiles
import os
import shutil
from app.users import auth_backend, current_active_user, fastapi_users

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@asynccontextmanager
async def span(app:FastAPI):
    await create_db()
    yield

app = FastAPI(lifespan=span)


app.mount("/files", StaticFiles(directory=UPLOAD_DIR), name="files")

app.include_router(fastapi_users.get_auth_router(auth_backend), prefix='/auth/jwt', tags=["auth"])
app.include_router(fastapi_users.get_register_router(UserRead, UserCreate), prefix='/auth', tags=["auth"])
app.include_router(fastapi_users.get_reset_password_router(), prefix='/auth', tags=["auth"])
app.include_router(fastapi_users.get_verify_router(UserRead), prefix='/auth', tags=["auth"])
app.include_router(fastapi_users.get_users_router(UserRead, UserUpdate), prefix='/users', tags=["users"])

@app.post("/upload")
async def upload_post(
        file: UploadFile  | None = File(None),
        caption:str=Form(""),
        user:User = Depends(current_active_user),
        session:AsyncSession=Depends(get_async_session)
        ):
    file_name = None
    file_url = None
    file_type = None
    if file is not None:
        filename = file.filename
        if filename is None:
            raise ValueError("filename is required")

        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        file_url = f"/files/{filename}"
        file_name = filename
        file_type = file.content_type

    post = Post(
            user_id = user.id,
            caption=caption,
            url=file_url,
            file_type=file_type,
            file_name=file_name
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


@app.get("/users")
async def get_users(session:AsyncSession=Depends(get_async_session)):
    result = await session.execute(select(User).order_by(User.created_at.desc()))
    users = []
    for r in result.all():
        users.append(r[0])

    return users

@app.get("/debug/headers")
async def debug_headers(request: Request):
    return dict(request.headers)


@app.delete("/posts/{post_id}")
async def delete_post(
        post_id:str,
        session:AsyncSession=Depends(get_async_session),
        user:User = Depends(current_active_user),
        ):
    try:
        post_uuid = uuid.UUID(post_id)
        result = await session.execute(select(Post).where(Post.id == post_uuid))
        post = result.scalars().first()

        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        if post.url is not None:
            filename = post.url.removeprefix("/files/")
            file_path = FSPath(UPLOAD_DIR) / filename

            print(file_path)

            if file_path.exists():
                file_path.unlink()

        await session.delete(post)
        await session.commit()

        return {"success": True, "message": "Post deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




