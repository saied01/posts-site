import uuid
from fastapi import Depends, Request, Response
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin, models
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
from fastapi_users.db import SQLAlchemyUserDatabase
from app.db import User, get_user_db
from dotenv import load_dotenv
import os

load_dotenv()
SECRET:str = os.environ["USERS_SECRET"]
JWT_LIFETIME:int = int(os.environ["JWT_LIFETIME"])

class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Request | None = None) -> None:
        print(user.email, user.id)

    async def on_after_login(self, user: User, request: Request | None = None, response: Response | None = None) -> None:
        if user.is_active:
            print("activo")
        else:
            print("not activo")
        # if not user.is_active:
        #     user.is_active = True
        #     await self.user_db.update(user)


async def get_user_manager(user_db:SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def get_jwt_strategy():
    return JWTStrategy(secret=SECRET, lifetime_seconds=JWT_LIFETIME)

auth_backend = AuthenticationBackend(
        name="jwt",
        transport=bearer_transport,
        get_strategy=get_jwt_strategy,
        )

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])
current_active_user = fastapi_users.current_user(active=True)
