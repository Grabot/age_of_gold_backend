from fastapi import Depends, Response
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.api_v1 import api_router_v1
from app.api.rest_util import get_failed_response
from app.api.util.util import get_user_tokens
from app.database import get_db
from app.models import User


@api_router_v1.post("/register", status_code=200)
async def register_user(
    email: str,
    user_name: str,
    password: str,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    if email is None or password is None or user_name is None:
        return get_failed_response("Invalid request", response)

    statement = select(User).where(func.lower(User.username) == user_name.lower())
    results = await db.execute(statement)
    result = results.first()

    if result is not None:
        return get_failed_response(
            "User is already taken, please choose a different one.", response
        )

    statement = select(User).where(User.origin == 0).where(func.lower(User.email) == email.lower())
    results = await db.execute(statement)
    result = results.first()

    if result is not None:
        return get_failed_response(
            "This email has already been used to create an account", response
        )

    user = User(username=user_name, email=email, origin=0)
    user.hash_password(password)
    [access_token, refresh_token] = get_user_tokens(user)
    db.add(user)
    await db.commit()
    # Refresh user so we can get the id.
    await db.refresh(user)

    return {
        "result": False,
        "message": "user created successfully.",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user.serialize,
    }
