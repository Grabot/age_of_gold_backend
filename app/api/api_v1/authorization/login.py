import hashlib
from typing import Any, Optional

from fastapi import Depends, Response
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.api_v1 import api_router_v1
from app.database import get_db
from app.models import User
from app.util.util import get_failed_response, get_user_tokens


class LoginRequest(BaseModel):
    email: Optional[str] = None
    user_name: Optional[str] = None
    password: str


@api_router_v1.post("/login", status_code=200)
async def login_user(
    login_request: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    email: Optional[str] = login_request.email
    user_name: Optional[str] = login_request.user_name
    password = login_request.password
    if password is None or (email is None and user_name is None):
        return get_failed_response("Invalid request", response)
    if user_name is None and email is not None:
        email_hash: str = hashlib.sha512(email.lower().encode("utf-8")).hexdigest()
        statement = (
            select(User).where(User.origin == 0).where(User.email_hash == email_hash)  # type: ignore  # noqa: E501
        )
        results = await db.execute(statement)
        result_user = results.first()
    elif email is None and user_name is not None:
        statement = (
            select(User)
            .where(User.origin == 0)
            .where(func.lower(User.username) == user_name.lower())
        )
        results = await db.execute(statement)
        result_user = results.first()
    else:
        return get_failed_response("Invalid request", response)

    if not result_user:
        return get_failed_response("user name or email not found", response)

    user: User = result_user.User

    if not user.verify_password(password):
        return get_failed_response("password not correct", response)

    user_token = get_user_tokens(user)
    db.add(user_token)
    await db.commit()

    login_response = {
        "result": True,
        "message": "user logged in successfully.",
        "access_token": user_token.access_token,
        "refresh_token": user_token.refresh_token,
        "user": user.serialize,
    }

    return login_response
