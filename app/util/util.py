import time
from typing import Any, Dict, Optional, TypedDict, Union

from authlib.jose import jwt
from authlib.jose.errors import DecodeError
from fastapi import Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.config.config import settings
from app.models import User
from app.models import UserToken


def get_failed_response(
    message: str, response: Response
) -> Dict[str, Union[bool, str]]:
    response.status_code = status.HTTP_200_OK
    actual_response: Dict[str, Union[bool, str]] = {
        "result": False,
        "message": message,
    }
    return actual_response


def get_user_tokens(
    user: User, access_expiration: int = 1800, refresh_expiration: int = 345600
) -> UserToken:
    token_expiration: int = int(time.time()) + access_expiration
    refresh_token_expiration: int = int(time.time()) + refresh_expiration
    access_token: str = user.generate_auth_token(access_expiration).decode("ascii")
    refresh_token: str = user.generate_refresh_token(refresh_expiration).decode("ascii")
    user_token: UserToken = UserToken(
        user_id=user.id,
        access_token=access_token,
        refresh_token=refresh_token,
        token_expiration=token_expiration,
        refresh_token_expiration=refresh_token_expiration,
    )
    return user_token


async def check_token(
    db: AsyncSession, token: str, retrieve_full: bool = False
) -> Optional[User]:
    token_statement = select(UserToken).filter_by(access_token=token)  # type: ignore
    results_token = await db.execute(token_statement)
    result_token = results_token.first()
    if result_token is None:
        return None
    user_token: UserToken = result_token.UserToken
    if user_token.token_expiration < int(time.time()):
        return None
    if retrieve_full:
        user_statement = select(User).filter_by(id=user_token.user_id)  # type: ignore
    else:
        user_statement = select(User).filter_by(id=user_token.user_id)  # type: ignore
    results = await db.execute(user_statement)
    result = results.first()
    if result is None:
        return None
    user: User = result.User
    return user


def get_auth_token(auth_header: Optional[str]) -> str:
    auth_token: str = ""
    if auth_header:
        auth_token = auth_header.split(" ")[1]
    return auth_token


async def delete_user_token_and_return(
    db: AsyncSession, user_token: UserToken, return_value: Optional[User]
) -> Optional[User]:
    await db.delete(user_token)
    await db.commit()
    return return_value


class JWTPayload(TypedDict):
    exp: int
    id: int
    user_name: str


async def refresh_user_token(
    db: AsyncSession, access_token: str, refresh_token: str
) -> Optional[User]:
    token_statement = (
        select(UserToken)
        .filter_by(access_token=access_token)  # type: ignore
        .filter_by(refresh_token=refresh_token)
    )
    results_token = await db.execute(token_statement)
    result_token = results_token.first()
    if result_token is None:
        return None
    user_token: UserToken = result_token.UserToken
    if user_token.refresh_token_expiration < int(time.time()):
        return await delete_user_token_and_return(db, user_token, None)
    user_statement = (
        select(User)
        .filter_by(id=user_token.user_id)  # type: ignore
        .options(selectinload(User.tokens))
    )
    user_results = await db.execute(user_statement)
    user_result = user_results.first()
    if user_result is None:
        return await delete_user_token_and_return(db, user_token, None)
    user: User = user_result.User
    if user_token.token_expiration > int(time.time()):
        return await delete_user_token_and_return(db, user_token, user)
    try:
        access: Dict[str, Any] = jwt.decode(access_token, settings.jwk)  # type: ignore
        refresh: Dict[str, Any] = jwt.decode(refresh_token, settings.jwk)  # type: ignore
    except DecodeError:
        return await delete_user_token_and_return(db, user_token, None)
    if not access or not refresh:
        return await delete_user_token_and_return(db, user_token, None)

    if refresh["exp"] < int(time.time()):
        return await delete_user_token_and_return(db, user_token, None)

    if user.id == access["id"] and user.username == refresh["user_name"]:
        return await delete_user_token_and_return(db, user_token, user)
    else:
        return await delete_user_token_and_return(db, user_token, None)
