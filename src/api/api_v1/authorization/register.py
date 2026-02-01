"""Endpoint for user registration."""

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from age_of_gold_worker.age_of_gold_worker.tasks import task_generate_avatar
from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models import User
from src.models.user import create_salt, hash_email
from src.util.decorators import handle_db_errors
from src.util.util import (
    SuccessfulLoginResponse,
    get_random_colour,
    get_successful_login_response,
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
    db: AsyncSession = Depends(get_db),
) -> SuccessfulLoginResponse:
    """Handle user registration request."""
    if not all(
        [register_request.email, register_request.username, register_request.password]
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request"
        )

    results = await db.execute(
        select(User).where(
            func.lower(User.username) == register_request.username.lower()
        )
    )
    if results.first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username already taken"
        )

    email_hash = hash_email(register_request.email)
    results = await db.execute(
        select(User).where(User.origin == 0, User.email_hash == email_hash)
    )
    if results.first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already used"
        )

    salt = create_salt()
    user = User(
        username=register_request.username,
        email_hash=email_hash,
        origin=0,
        salt=salt,
        password_hash=hash_password(register_request.password + salt),
        colour=get_random_colour()
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    user_token = get_user_tokens(user)
    db.add(user_token)
    s3_key = user.avatar_s3_key(user.avatar_filename_default())
    await db.commit()
    _ = task_generate_avatar.delay(
        user.avatar_filename(),
        s3_key,
        user.id,
    )

    return await get_successful_login_response(user_token, user, db)
