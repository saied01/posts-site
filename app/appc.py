import uuid
from pathlib import Path as FSPath
from fastapi import FastAPI, HTTPException, File, Path, UploadFile, Form, Depends, Request, APIRouter
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import UserCreate, UserRead, UserUpdate
from app.db import Post, create_db,get_async_session, User
from contextlib import asynccontextmanager
from sqlalchemy import select
import os
import shutil
from app.users import auth_backend, current_active_user, fastapi_users
from configs.config import UPLOAD_DIR
from services.file_processing import get_storage_name, normalize_filename


@asynccontextmanager
async def span(app:FastAPI):
    await create_db()
    yield

app = FastAPI(lifespan=span)

router = APIRouter(prefix="/files", dependencies=[Depends(current_active_user)])

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
    storage_name = None
    storage_path = None
    file_type = None
    status = "none"
    if file is not None:
        filename = file.filename
        if filename is None:
            raise ValueError("filename is required")


        storage_name = get_storage_name(filename)
        storage_path = os.path.join(UPLOAD_DIR,storage_name)
        file_name = normalize_filename(filename)
        file_type = file.content_type


        with open(storage_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        status = "uploaded"


    post = Post(
            user_id = user.id,
            caption=caption,
            file_type=file_type,
            file_name=file_name,
            file_storage_path = str(storage_path),
            file_storage_name = storage_name,
            file_status = status
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

        if post.file_storage_path is not None:
            filename = post.file_storage_name
            file_path = FSPath(UPLOAD_DIR) / filename

            print(file_path)

            if file_path.exists():
                file_path.unlink()

        await session.delete(post)
        await session.commit()

        return {"success": True, "message": "Post deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{post_id}")
async def download_post_file(
        post_id:str,
        session:AsyncSession=Depends(get_async_session),
        user:User=Depends(current_active_user)
        ):
    post_uuid = uuid.UUID(post_id)
    result = await session.execute(select(Post).where(Post.id == post_uuid))
    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if str(post.file_status) != "uploaded":
        raise HTTPException(status_code=409, detail="File not ready")

    path = post.file_storage_path
    path = FSPath(str(path))

    if not path.exists():
        raise HTTPException(status_code=410, detail="File missing")


    return FileResponse(
            path=path,
            media_type=str(post.file_type),
            filename=str(post.file_name),
            )


app.include_router(router)
