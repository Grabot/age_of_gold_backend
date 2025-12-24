"""Login user with oauth2"""

import re

from fastapi import HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Select
from sqlmodel import select

from age_of_gold_worker.age_of_gold_worker.tasks import task_generate_avatar
from src.config.config import settings
from src.models.user import User, hash_email
from src.sockets.sockets import redis


async def validate_oauth_state(
    state: str,
) -> None:
    """
    Validate the OAuth state parameter and delete it from Redis.
    Raises HTTPException if the state is invalid.
    """
    if not await redis.exists(f"oauth_state:{state}"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state",
        )
    await redis.delete(f"oauth_state:{state}")


def _sanitize_username(username: str) -> str:
    """Remove '@' from username if it looks like an email."""
    if re.match(
        r"^[a-zA-Z0-9.a-zA-Z0-9.!#$%&'*+-/=?^_`{|}~]+@[a-zA-Z0-9]+\.[a-zA-Z]+", username
    ):
        return username.replace("@", "")
    return username


async def _find_available_username(db: AsyncSession, username: str) -> str:
    """Find an available username by appending a number if necessary."""
    new_user_name = username
    index = 2
    while index < 100:
        statement_name_new: Select = select(User).where(
            func.lower(User.username) == new_user_name.lower()
        )
        results_name_new = await db.execute(statement_name_new)
        result_username_new = results_name_new.first()
        if not result_username_new:
            break
        new_user_name = f"{username}_{index}"
        index += 1
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Couldn't create the user",
        )
    return new_user_name


async def _create_user(
    db: AsyncSession, username: str, hashed_email: str, origin: int
) -> tuple[User, bool]:
    """Create a new user if the username is available, otherwise find an available username."""
    new_user_name = await _find_available_username(db, username)
    user = User(
        username=new_user_name,
        email_hash=hashed_email,
        password_hash="",
        salt="",
        origin=origin,
    )
    db.add(user)
    await db.commit()
    return user, True


async def login_user_oauth(
    username: str,
    email: str,
    origin: int,
    db: AsyncSession,
) -> User:
    """Login user with OAuth2"""
    username = _sanitize_username(username)
    hashed_email = hash_email(email)

    statement_origin: Select = (
        select(User).where(User.origin == origin).where(User.email_hash == hashed_email)
    )
    results_origin = await db.execute(statement_origin)
    result_user_origin = results_origin.first()

    if result_user_origin:
        user: User = result_user_origin.User
        user_created = False
    else:
        user, user_created = await _create_user(db, username, hashed_email, origin)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User creation failed",
        )

    if user_created:
        await db.refresh(user)
        s3_key = user.avatar_s3_key(user.avatar_filename_default())
        task_generate_avatar.delay(user.avatar_filename(), s3_key, user.id)

    return user


def redirect_oauth(access_token: str) -> RedirectResponse:
    """Redirects the user to the frontend URL with the access token as a query parameter."""
    redirect_url = f"{settings.FRONTEND_URL}/auth/callback?token={access_token}"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
