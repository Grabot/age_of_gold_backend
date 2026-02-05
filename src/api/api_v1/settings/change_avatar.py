"""Endpoint for changing avatar."""

from typing import Dict, Optional, Tuple

from fastapi import Depends, HTTPException, Security, UploadFile, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models.user import User
from src.models.user_token import UserToken
from src.util.decorators import handle_db_errors
from src.util.gold_logging import logger
from src.util.security import checked_auth_token
from src.util.rest_util import update_friend_versions_and_notify

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
MAX_AVATAR_SIZE = 4 * 1024 * 1024  # 4MB


@api_router_v1.patch("/user/avatar", status_code=200, response_model=dict)
@handle_db_errors("Changing avatar failed")
async def change_avatar(
    request: Request,
    avatar: Optional[UploadFile] = None,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, bool]:
    """Handle change avatar request."""
    me, _ = user_and_token

    s3_client = request.app.state.s3
    cipher = request.app.state.cipher

    if not avatar:
        me.remove_avatar(s3_client)
        me.default_avatar = True
        me.avatar_version += 1
        db.add(me)

        # Update friend versions and notify about avatar change
        await update_friend_versions_and_notify(
            db,
            me.id,  # type: ignore[arg-type]
            "avatar_updated",
            {"user_id": me.id},
        )

        await db.commit()
        return {"success": True}

    if not avatar.size or not avatar.filename:
        raise HTTPException(status_code=400, detail="Invalid avatar file")
    if avatar.size > MAX_AVATAR_SIZE:
        raise HTTPException(status_code=400, detail="Avatar too large (max 4MB)")
    if avatar.filename.split(".")[-1].lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PNG/JPG allowed")

    avatar_bytes = await avatar.read()
    logger.info("Avatar creation in bucket")
    me.create_avatar(s3_client, cipher, avatar_bytes)
    me.avatar_version += 1

    if me.default_avatar:
        me.default_avatar = False
    db.add(me)

    await update_friend_versions_and_notify(
        db,
        me.id,  # type: ignore[arg-type]
        "avatar_updated",
        {"user_id": me.id},
    )

    await db.commit()

    logger.info("User %s changed their avatar", me.username)
    return {
        "success": True,
    }
