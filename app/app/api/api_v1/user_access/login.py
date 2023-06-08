from copy import copy
from typing import Optional

from fastapi import Depends, Response
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select
from util.util import get_user_tokens

from app.api.api_v1 import api_router_v1
from app.api.rest_util import get_failed_response
from app.database import get_db
from app.models import User


class LoginRequest(BaseModel):
    email: Optional[str] = None
    user_name: Optional[str] = None
    password: str


@api_router_v1.post("/login", status_code=200)
async def login_user(
    login_request: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    email = login_request.email
    user_name = login_request.user_name
    password = login_request.password
    if password is None or (email is None and user_name is None):
        return get_failed_response("Invalid request", response)
    if user_name is None:
        # login with email
        statement = (
            select(User)
            .where(User.origin == 0)
            .where(func.lower(User.email) == email.lower())
            .options(selectinload(User.friends))
            .options(selectinload(User.followers))
        )
        results = await db.execute(statement)
        result_user = results.first()
    elif email is None:
        statement = (
            select(User)
            .where(User.origin == 0)
            .where(func.lower(User.username) == user_name.lower())
            .options(selectinload(User.friends))
            .options(selectinload(User.followers))
        )
        results = await db.execute(statement)
        result_user = results.first()
    else:
        return get_failed_response("Invalid request", response)

    if not result_user:
        return get_failed_response("user name or email not found", response)

    user = result_user.User
    return_user = copy(user.serialize)

    if not user.verify_password(password):
        return get_failed_response("password not correct", response)
    print("verification was successful!")
    # Valid login, we refresh the token for this user.
    [access_token, refresh_token] = get_user_tokens(user)
    db.add(user)
    await db.commit()

    # We don't refresh the user object because we know all we want to know
    login_response = {
        "result": True,
        "message": "user logged in successfully.",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": return_user,
    }

    return login_response
