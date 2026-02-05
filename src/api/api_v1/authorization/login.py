"""endpoint for login"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models import User
from src.models.user import hash_email
from src.util.decorators import handle_db_errors
from src.util.gold_logging import logger
from src.util.util import (
    SuccessfulLoginResponse,
    get_successful_login_response,
    get_user_tokens,
)


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Retrieve a user by their email address."""
    email_hash = hash_email(email)
    user: Optional[User] = (
        await db.execute(
            select(User)
            .where(User.origin == 0, User.email_hash == email_hash)
            .options(selectinload(User.tokens))  # type: ignore
        )
    ).scalar_one_or_none()
    return user


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """Retrieve a user by their username."""
    user: Optional[User] = (
        await db.execute(
            select(User)
            .where(User.origin == 0, func.lower(User.username) == username.lower())
            .options(selectinload(User.tokens))  # type: ignore
        )
    ).scalar_one_or_none()
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
    db: AsyncSession = Depends(get_db),
) -> SuccessfulLoginResponse:
    """Handle user login request."""
    user: Optional[User] = None
    if login_request.email and login_request.password:
        user = await get_user_by_email(db, login_request.email)
    elif login_request.username and login_request.password:
        user = await get_user_by_username(db, login_request.username)
    else:
        logger.warning("Login failed: Invalid request")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request"
        )

    if not user:
        logger.warning("Login failed: User not found or invalid credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email/username or password",
        )

    password_with_salt = login_request.password + user.salt
    if not user.verify_password(user.password_hash, password_with_salt):
        logger.warning("Login failed for user: %s (invalid password)", user.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email/username or password",
        )

    user_token = get_user_tokens(user)
    db.add(user_token)
    await db.commit()
    logger.info("User logged in: %s", user.username)

    return await get_successful_login_response(user_token, user, db)
