"""Endpoint for user logout."""

from typing import Any, Tuple

from fastapi import Depends, HTTPException, Response, Security, status
from sqlalchemy.ext.asyncio import AsyncSession

import os
from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models.user import User
from src.models.user_token import UserToken
from src.util.decorators import handle_db_errors
from src.util.gold_logging import logger
from src.util.security import check_token, checked_auth_token, get_valid_auth_token
from src.config.config import settings

@api_router_v1.post("/user/avatar", status_code=200)
@handle_db_errors("Logout failed")
async def get_avatar(
    response: Response,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Handle user logout request."""
    user, _ = user_and_token
    file_folder = settings.UPLOAD_FOLDER_AVATARS
    print(f"file folder {file_folder}")
    if user.default_avatar:
        file_name = user.avatar_filename_default()
    else:
        file_name = user.avatar_filename()
    print(f"file_name {file_name}")

    file_path = os.path.join(file_folder, "%s.png" % file_name)
    print(f"file_path {file_path}")

    if not os.path.isfile(file_path):
        print("failed")
        # TODO": Can this be improved?
        return Response(
            content="An error occurred",
            media_type="text/plain",
            status_code=500
        )
    else:
        print("reading")
        with open(file_path, "rb") as fd:
            print(f"read")
            avatar_bytes = fd.read()

        logger.info("User %s got their avatar", user.username)
        print("sending")
        return Response(
            content=avatar_bytes,
            media_type="image/png"  # or "image/jpeg", etc.
        )
