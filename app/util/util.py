import time
from typing import Any, Dict, Optional, Tuple, TypedDict, Union

import jwt as pyjwt
from argon2 import PasswordHasher
from fastapi import Response, status
from jwt.exceptions import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession  # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.sql.selectable import Select
from sqlmodel import select

from app.config.config import settings
from app.models import User, UserToken

ph = PasswordHasher()


def get_failed_response(
    message: str,
    response: Response,
    status_code: int = status.HTTP_400_BAD_REQUEST,
) -> Dict[str, Union[bool, str]]:
    response.status_code = status_code
    return {
        "result": False,
        "message": message,
    }


def get_user_tokens(
    user: User, access_expiration: int = 1800, refresh_expiration: int = 345600
) -> UserToken:
    token_expiration: int = int(time.time()) + access_expiration
    refresh_token_expiration: int = int(time.time()) + refresh_expiration
    access_token: str = user.generate_auth_token(access_expiration)
    refresh_token: str = user.generate_refresh_token(refresh_expiration)
    if user.id is None:
        raise ValueError("User ID should not be None")
    user_token: UserToken = UserToken(
        user_id=user.id,
        access_token=access_token,
        refresh_token=refresh_token,
        token_expiration=token_expiration,
        refresh_token_expiration=refresh_token_expiration,
    )
    return user_token


async def check_token(
    db: AsyncSession, token: str
) -> Tuple[Optional[User], Optional[UserToken]]:
    token_statement: Select = (
        select(UserToken)
        .options(joinedload(UserToken.user))
        .filter_by(access_token=token)
    )
    results_token = await db.execute(token_statement)
    result_token = results_token.first()
    if result_token is None:
        return None, None
    user_token: UserToken = result_token.UserToken
    if user_token.token_expiration < int(time.time()):
        return None, None

    user: User = user_token.user
    return user, user_token


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
    token_statement: Select = (
        select(UserToken)
        .filter_by(access_token=access_token)
        .filter_by(refresh_token=refresh_token)
    )
    results_token = await db.execute(token_statement)
    result_token = results_token.first()
    if result_token is None:
        return None
    user_token: UserToken = result_token.UserToken
    if user_token.refresh_token_expiration < int(time.time()):
        return await delete_user_token_and_return(db, user_token, None)
    user_statement: Select = (
        select(User).filter_by(id=user_token.user_id).options(selectinload(User.tokens))
    )
    user_results = await db.execute(user_statement)
    user_result = user_results.first()
    if user_result is None:
        return await delete_user_token_and_return(db, user_token, None)
    user: User = user_result.User
    if user_token.token_expiration > int(time.time()):
        return await delete_user_token_and_return(db, user_token, user)
    try:
        access: Dict[str, Any] = pyjwt.decode(
            access_token,
            settings.jwk_pem,
            algorithms=[settings.header["alg"]],
            options={"verify_aud": False},
        )
        refresh: Dict[str, Any] = pyjwt.decode(
            refresh_token,
            settings.jwk_pem,
            algorithms=[settings.header["alg"]],
            options={"verify_aud": False},
        )
    except InvalidTokenError:
        return await delete_user_token_and_return(db, user_token, None)
    if user.id == access["id"] and user.username == refresh["user_name"]:
        return await delete_user_token_and_return(db, user_token, user)
    else:
        return await delete_user_token_and_return(db, user_token, None)


def hash_password(password: str) -> str:
    return ph.hash(password)
