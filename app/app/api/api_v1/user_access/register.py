from typing import Optional

from fastapi import Depends, Response
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from util.util import get_user_tokens

from app.api.api_v1 import api_router_v1
from app.api.rest_util import get_failed_response
from app.database import get_db
from app.models import User


class RegisterRequest(BaseModel):
    email: Optional[str] = None
    user_name: Optional[str] = None
    password: str


@api_router_v1.post("/register", status_code=200)
async def register_user(
    register_request: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    print("starting register")
    email = register_request.email
    user_name = register_request.user_name
    password = register_request.password

    if email is None or password is None or user_name is None:
        return get_failed_response("Invalid request", response)

    print("all fields present, starting first query")
    # Not loading the friends and followers here. Just checking if the username is taken.
    statement = select(User).where(func.lower(User.username) == user_name.lower())
    results = await db.execute(statement)
    result = results.first()

    print(f"results: {result}")
    if result is not None:
        return get_failed_response(
            "User is already taken, please choose a different one.", response
        )

    print("starting second statement")
    # Also not loading the friends and followers here, just checking if the email is taken.
    statement = select(User).where(User.origin == 0).where(func.lower(User.email) == email.lower())
    results = await db.execute(statement)
    result = results.first()

    print(f"results: {result}")
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

    # Return the user with no friend information because they have none yet.
    return {
        "result": True,
        "message": "user created successfully.",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user.serialize_get,
    }
