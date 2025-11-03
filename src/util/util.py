import time
from typing import Dict, Optional, Union

from argon2 import PasswordHasher
from fastapi import Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Select
from sqlmodel import select

from src.models import User, UserToken

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


def get_successful_user_response(
    user: User,
    user_token: UserToken,
) -> Dict[str, Union[bool, str, Dict[str, Union[Optional[int], str]]]]:
    return {
        "result": True,
        "access_token": user_token.access_token,
        "refresh_token": user_token.refresh_token,
        "user": user.serialize,
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


async def delete_user_token_and_return(
    db: AsyncSession, user_token: UserToken, return_value: Optional[User]
) -> Optional[User]:
    await db.delete(user_token)
    await db.commit()
    return return_value


async def refresh_user_token(
    db: AsyncSession, access_token: str, refresh_token: str
) -> Optional[User]:
    token_statement: Select = (
        select(UserToken)
        .where(UserToken.access_token == access_token)
        .where(UserToken.refresh_token == refresh_token)
    )
    results_token = await db.execute(token_statement)
    result_token = results_token.first()
    if result_token is None:
        return None
    user_token: UserToken = result_token.UserToken
    if user_token.refresh_token_expiration < int(time.time()):
        return await delete_user_token_and_return(db, user_token, None)
    user_statement: Select = select(User).where(User.id == user_token.user_id)
    user_results = await db.execute(user_statement)
    user_result = user_results.first()
    if user_result is None:
        return await delete_user_token_and_return(db, user_token, None)
    user: User = user_result.User
    return await delete_user_token_and_return(db, user_token, user)


def hash_password(password: str) -> str:
    return ph.hash(password)
