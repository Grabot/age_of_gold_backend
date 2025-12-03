"""Endpoint for getting user avatar."""

import os
from typing import Tuple

from fastapi import Depends, HTTPException, Security, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.router import api_router_v1
from src.config.config import settings
from src.database import get_db
from src.models.user import User
from src.models.user_token import UserToken
from src.util.decorators import handle_db_errors
from src.util.gold_logging import logger
from src.util.security import checked_auth_token


@api_router_v1.get("/user/avatar", status_code=200)
@handle_db_errors("Get avatar failed")
async def get_avatar(
    get_default: bool = False,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """Handle get avatar request."""
    user, _ = user_and_token
    file_folder = settings.UPLOAD_FOLDER_AVATARS

    if user.default_avatar or get_default:
        file_name = user.avatar_filename_default() + ".png"
    else:
        file_name = user.avatar_filename() + ".png"

    file_path = os.path.join(file_folder, file_name)

    if not os.path.isfile(file_path):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred",
        )

    logger.info("User %s got their avatar", user.username)
    return FileResponse(file_path)
