"""Endpoint for changing avatar."""

from typing import Dict, Optional, Tuple

from fastapi import Depends, HTTPException, Security, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models.user import User
from src.models.user_token import UserToken
from src.util.decorators import handle_db_errors
from src.util.gold_logging import logger
from src.util.security import checked_auth_token

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2MB


@api_router_v1.patch("/user/avatar", status_code=200, response_model=dict)
@handle_db_errors("Changing avatar failed")
async def change_avatar(
    avatar: Optional[UploadFile] = None,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, bool]:
    """Handle change avatar request."""
    user, _ = user_and_token

    if not avatar:
        # TODO: remove not default image?
        user.remove_avatar()
        user.default_avatar = True
        db.add(user)
        await db.commit()
        return {"success": True}

    if not avatar.size or not avatar.filename:
        raise HTTPException(status_code=400, detail="Invalid avatar file")
    if avatar.size > MAX_AVATAR_SIZE:
        raise HTTPException(status_code=400, detail="Avatar too large (max 2MB)")
    if avatar.filename.split(".")[-1].lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PNG/JPG allowed")

    avatar_bytes = await avatar.read()
    user.create_avatar(avatar_bytes)

    if user.default_avatar:
        user.default_avatar = False
        db.add(user)
        await db.commit()

    logger.info("User %s changed their avatar", user.username)
    return {
        "success": True,
    }
