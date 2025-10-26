"""Endpoint for user registration."""

import asyncio
from typing import Any

from fastapi import Depends, Response, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.api.api_v1 import api_router_v1
from src.celery_worker.tasks import task_generate_avatar
from src.config.config import settings
from src.database import get_db
from src.models import User
from src.models.user import avatar_filename, create_salt, hash_email
from src.sockets.sockets import sio
from src.util.decorators import handle_db_errors
from src.util.util import (
    get_failed_response,
    get_successful_user_response,
    get_user_tokens,
    hash_password,
)


class RegisterRequest(BaseModel):
    """Request model for user registration."""

    email: str
    username: str
    password: str


@api_router_v1.post("/register", status_code=201)
@handle_db_errors("Registration failed")
async def register_user(
    register_request: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Handle user registration request."""
    if not all(
        [register_request.email, register_request.username, register_request.password]
    ):
        return get_failed_response(
            "Invalid request", response, status.HTTP_400_BAD_REQUEST
        )

    results = await db.execute(
        select(User).where(
            func.lower(User.username) == register_request.username.lower()
        )
    )
    if results.first():
        return get_failed_response(
            "Username already taken", response, status.HTTP_409_CONFLICT
        )

    email_hash = hash_email(register_request.email, settings.PEPPER)
    results = await db.execute(
        select(User).where(User.origin == 0, User.email_hash == email_hash)
    )
    if results.first():
        return get_failed_response(
            "Email already used", response, status.HTTP_409_CONFLICT
        )

    salt = create_salt()
    user = User(
        username=register_request.username,
        email_hash=email_hash,
        origin=0,
        salt=salt,
        password_hash=hash_password(register_request.password + salt),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    user_token = get_user_tokens(user)
    db.add(user_token)
    await db.commit()

    task_generate_avatar.delay(avatar_filename(), user.id)
    return get_successful_user_response(user, user_token)


class AvatarCreatedRequest(BaseModel):
    """Request model for avatar creation notification."""

    user_id: int


@api_router_v1.post("/avatar/created", status_code=200)
async def avatar_created(
    avatar_created_request: AvatarCreatedRequest,
) -> dict[str, Any]:
    """Handle avatar creation notification."""
    user_id = avatar_created_request.user_id
    room = f"room_{user_id}"

    await asyncio.sleep(1)

    await sio.emit(
        "message_event",
        "Avatar creation done!",
        room=room,
    )

    return {
        "result": True,
        "message": "Avatar creation done!",
    }
