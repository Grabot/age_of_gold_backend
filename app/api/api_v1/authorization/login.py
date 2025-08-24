from typing import Any, Optional

from fastapi import Depends, Response, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession  # pyright: ignore[reportMissingImports]
from sqlmodel import select

from app.api.api_v1 import api_router_v1
from app.config.config import settings
from app.database import get_db
from app.models import User
from app.models.user import hash_email
from app.util.util import get_failed_response, get_user_tokens

from sqlalchemy.exc import SQLAlchemyError
from app.util.gold_logging import logger


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    email_hash = hash_email(email, settings.PEPPER)
    results_user = await db.execute(
        select(User).where(User.origin == 0, User.email_hash == email_hash)
    )
    result_user = results_user.first()
    if result_user is None:
        return None
    else:
        user: User = result_user.User
        return user


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    results_user = await db.execute(
        select(User).where(
            User.origin == 0, func.lower(User.username) == username.lower()
        )
    )
    result_user = results_user.first()
    if result_user is None:
        return None
    else:
        user: User = result_user.User
        return user


class LoginRequest(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: str


@api_router_v1.post("/login", status_code=200)
async def login_user(
    login_request: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    if not login_request.password or not (
        login_request.email or login_request.username
    ):
        logger.warning("Login failed: Invalid request (missing credentials)")
        return get_failed_response(
            "Invalid request", response, status.HTTP_400_BAD_REQUEST
        )

    try:
        user: Optional[User] = None
        if login_request.email:
            user = await get_user_by_email(db, login_request.email)
        elif login_request.username:
            user = await get_user_by_username(db, login_request.username)

        if not user:
            logger.warning("Login failed: User not found or invalid credentials")
            return get_failed_response(
                "Invalid email/username or password",
                response,
                status.HTTP_401_UNAUTHORIZED,
            )

        password_with_salt = login_request.password + user.salt
        if not user.verify_password(user.password_hash, password_with_salt):
            logger.warning(f"Login failed for user: {user.username} (invalid password)")
            return get_failed_response(
                "Invalid email/username or password",
                response,
                status.HTTP_401_UNAUTHORIZED,
            )

        user_token = get_user_tokens(user)
        db.add(user_token)
        await db.commit()
        logger.info(f"User logged in: {user.username}")

        return {
            "result": True,
            "message": "User logged in successfully.",
            "access_token": user_token.access_token,
            "refresh_token": user_token.refresh_token,
            "user": user.serialize,
        }

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Database error during login: {e}")
        return get_failed_response(
            "Internal server error", response, status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error during login: {e}")
        return get_failed_response(
            "Internal server error", response, status.HTTP_500_INTERNAL_SERVER_ERROR
        )
