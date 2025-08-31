import asyncio
from typing import Any

from fastapi import Depends, Response, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession  # pyright: ignore[reportMissingImports]
from sqlmodel import select

from app.api.api_v1 import api_router_v1
from app.celery_worker.tasks import task_generate_avatar
from app.config.config import settings
from app.database import get_db
from app.models import User
from app.models.user import avatar_filename, create_salt, hash_email
from app.sockets.sockets import sio
from app.util.gold_logging import logger
from app.util.util import get_failed_response, get_user_tokens, hash_password


class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str


@api_router_v1.post("/register", status_code=201)
async def register_user(
    register_request: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    if not all(
        [register_request.email, register_request.username, register_request.password]
    ):
        return get_failed_response(
            "Invalid request", response, status.HTTP_400_BAD_REQUEST
        )

    try:
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

        task_generate_avatar.delay(avatar_filename(), user.id)  # type: ignore

        return {
            "result": True,
            "message": "User created successfully.",
            "access_token": user_token.access_token,
            "refresh_token": user_token.refresh_token,
            "user": user.serialize,
        }

    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Database integrity error during registration: {e}")
        return get_failed_response(
            "Database error (e.g., duplicate key)", response, status.HTTP_409_CONFLICT
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Database error during registration: {e}")
        return get_failed_response(
            "Database error", response, status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error during registration: {e}")
        return get_failed_response(
            "Internal server error", response, status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class AvatarCreatedRequest(BaseModel):
    user_id: int


@api_router_v1.post("/avatar/created", status_code=200)
async def avatar_created(
    avatar_created_request: AvatarCreatedRequest,
) -> dict[str, Any]:
    user_id = avatar_created_request.user_id
    room = "room_%s" % user_id

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
