"""endpoint for login"""

from typing import Any, Optional

from fastapi import Depends, Response, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.api.api_v1 import api_router_v1
from src.config.config import settings
from src.database import get_db
from src.models import User
from src.models.user import hash_email
from src.util.decorators import handle_db_errors
from src.util.gold_logging import logger
from src.util.util import (
    get_failed_response,
    get_successful_user_response,
    get_user_tokens,
)


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Retrieve a user by their email address."""
    email_hash = hash_email(email, settings.PEPPER)
    results_user = await db.execute(
        select(User).where(User.origin == 0, User.email_hash == email_hash)
    )
    result_user = results_user.first()
    if result_user is None:
        return None

    user: User = result_user.User
    return user


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """Retrieve a user by their username."""
    results_user = await db.execute(
        select(User).where(
            User.origin == 0, func.lower(User.username) == username.lower()
        )
    )
    result_user = results_user.first()
    if result_user is None:
        return None

    user: User = result_user.User
    return user


class LoginRequest(BaseModel):
    """Request model for user login."""

    email: Optional[str] = None
    username: Optional[str] = None
    password: str


@api_router_v1.post("/login", status_code=200)
@handle_db_errors("Login failed")
async def login_user(
    login_request: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Handle user login request."""
    if not login_request.password or not (
        login_request.email or login_request.username
    ):
        logger.warning("Login failed: Invalid request (missing credentials)")
        return get_failed_response(
            "Invalid request", response, status.HTTP_400_BAD_REQUEST
        )

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
        logger.warning("Login failed for user: %s (invalid password)", user.username)
        return get_failed_response(
            "Invalid email/username or password",
            response,
            status.HTTP_401_UNAUTHORIZED,
        )

    user_token = get_user_tokens(user)
    db.add(user_token)
    await db.commit()
    logger.info("User logged in: %s", user.username)

    return get_successful_user_response(user, user_token)
