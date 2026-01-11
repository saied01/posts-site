from collections.abc import AsyncGenerator
import uuid

from fastapi import Depends
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Table, null, true
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime
from fastapi_users.db import SQLAlchemyBaseUserTableUUID, SQLAlchemyUserDatabase, SQLAlchemyBaseOAuthAccountTableUUID

DATABASE_URL = "sqlite+aiosqlite:///./test.db"

class Base(DeclarativeBase):
    pass


user_follows = Table(
        "user_follows",
        Base.metadata,
        Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True),
        Column("friend_id", UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
        )


class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "users"

    posts = relationship("Post", back_populates="user")
    # following = relationship(
    #         "User",
    #         secondary=user_follows,
    #         primaryjoin=lambda: User.id == user_follows.c.user_id,
    #         secondaryjoin=lambda: User.id == user_follows.c.friend_id,
    #     )


class Post(Base):
    __tablename__ = "posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    caption = Column(Text, nullable=False)
    url = Column(String, nullable=True)
    file_type = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    file_name = Column(String, nullable=True)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="posts")



engine = create_async_engine(DATABASE_URL)
async_s_maker = async_sessionmaker(engine, expire_on_commit=False)

async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_async_session():
    async with async_s_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)
