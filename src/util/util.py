import random
import time
from io import BytesIO
from typing import Any, List, Optional, TypedDict

from argon2 import PasswordHasher
from botocore.exceptions import ClientError
from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.selectable import Select
from sqlmodel import select

from src.config.config import settings
from src.models import Chat, User, UserToken
from src.util.gold_logging import logger
from src.util.storage_util import download_image

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
        "#ED64A6",
        "#F6AD55",
        "#FC8181",
        "#667EEA",
        "#764BA2",
        "#F093FB",
        "#4FACFE",
        "#00C9A7",
        "#8BD3DD",
        "#A5DD9B",
        "#F9D71C",
    ]
    return random.choice(colors)


def create_avatar_streaming_response(
    s3_client: Any, cipher: Any, s3_key: str, file_name: str, encrypted: bool
) -> StreamingResponse:
    """Create a streaming response for avatar images.

    Args:
        s3_client: S3 client for downloading the image
        cipher: Cipher for decryption if needed
        s3_key: S3 key for the image
        file_name: File name for the response
        encrypted: Whether the image is encrypted

    Returns:
        StreamingResponse: FastAPI streaming response with the image

    Raises:
        HTTPException: If avatar is not found or download fails
    """
    try:
        decrypted_data: bytes = download_image(
            s3_client, cipher, settings.S3_BUCKET_NAME, s3_key, encrypted
        )
        decrypted_buffer: BytesIO = BytesIO(decrypted_data)
        decrypted_buffer.seek(0)
        return StreamingResponse(
            decrypted_buffer,
            media_type="image/png",
            headers={"Content-Disposition": f"inline; filename={file_name}"},
        )
    except ClientError as e:
        logger.error("Failed to fetch avatar: %s", str(e))
        if e.response["Error"]["Code"] == "NoSuchKey":
            raise HTTPException(status_code=404, detail="Avatar not found") from e
        raise HTTPException(status_code=500, detail="Failed to fetch avatar") from e


async def get_chat_and_verify_admin(
    db: AsyncSession,
    group_id: int,
    user_id: int,
    require_admin: bool = True,
    permission_error_detail: str = "Only group admins can perform this action",
) -> Chat:
    """Get a chat and verify if the user is an admin.

    Args:
        db: Database session
        group_id: Group ID to check
        user_id: User ID to verify
        require_admin: Whether admin rights are required
        permission_error_detail: Custom error message for permission denial

    Returns:
        Chat: The chat object

    Raises:
        HTTPException: If group not found or user doesn't have required permissions
    """
    chat_statement: Select = (
        select(Chat).where(Chat.id == group_id).options(selectinload(Chat.groups))  # type: ignore
    )
    chat: Chat = (await db.execute(chat_statement)).scalar_one()

    # Check if current user has required permissions
    if require_admin and user_id not in chat.user_admin_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=permission_error_detail,
        )

    return chat
