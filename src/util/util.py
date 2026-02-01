import time
from typing import Any, List, Optional, TypedDict

from argon2 import PasswordHasher
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Select
from sqlmodel import select
import random

from src.models import User, UserToken

ph = PasswordHasher()


class LoginData(TypedDict):
    access_token: str
    refresh_token: str
    profile_version: int
    avatar_version: int
    friends: List[dict[str, Any]]
    groups: List[dict[str, Any]]


class SuccessfulLoginResponse(TypedDict):
    success: bool
    data: LoginData


async def get_successful_login_response(
    user_token: UserToken, user: User, db: AsyncSession
) -> SuccessfulLoginResponse:
    # Load friends using the existing User.friends relationship
    # First refresh the user object to get the latest data
    await db.refresh(user, ["friends", "groups"])

    # Serialize friends data from the loaded relationship
    friends_data = []
    for friend in user.friends:
        friends_data.append(
            {
                "friend_id": friend.friend_id,
                "friend_version": friend.friend_version,
            }
        )

    # Serialize groups data from the loaded relationship
    groups_data = []
    for group in user.groups:
        groups_data.append(
            {
                "group_id": group.group_id,
                "group_version": group.group_version,
            }
        )

    return {
        "success": True,
        "data": {
            "access_token": user_token.access_token,
            "refresh_token": user_token.refresh_token,
            "profile_version": user.profile_version,
            "avatar_version": user.avatar_version,
            "friends": friends_data,
            "groups": groups_data,
        },
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


def get_user_room(user_id: int) -> str:
    return f"room_{user_id}"

def get_group_room(group_id: int) -> str:
    return f"group_{group_id}"

def get_random_colour() -> str:
    colors = [
        '#FF6B6B',
        '#FF8E53',
        '#FFC154',
        '#48CF85',
        '#4299E1',
        '#5677FC',
        '#9013FE',
        '#ED64A6',
        '#F6AD55',
        '#FC8181',
        '#667EEA',
        '#764BA2',
        '#F093FB',
        '#4FACFE',
        '#00C9A7',
        '#8BD3DD',
        '#A5DD9B',
        '#F9D71C'
    ]
    return random.choice(colors)