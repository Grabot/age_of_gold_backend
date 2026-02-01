"""Endpoint for getting user avatar."""

from typing import Dict, Tuple, Any, Optional
from pydantic import BaseModel

from fastapi import Depends, HTTPException, Security, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models.user import User
from src.models.user_token import UserToken
from src.util.decorators import handle_db_errors
from src.util.security import checked_auth_token
from src.util.rest_util import get_user_from_db
from src.util.util import create_avatar_streaming_response


class AvatarRequest(BaseModel):
    """Request model for getting user avatar."""

    user_id: Optional[int] = None
    get_default: Optional[bool] = None


@api_router_v1.post("/user/avatar", status_code=200)
@handle_db_errors("Get avatar failed")
async def get_avatar(
    request: Request,
    avatar_request: AvatarRequest,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Handle get avatar request for the authenticated user or any user by ID."""
    user, _ = user_and_token
    s3_client: Any = request.app.state.s3
    cipher: Any = request.app.state.cipher

    target_user_id = avatar_request.user_id
    target_user: User | None = None
    if target_user_id is None:
        target_user = user
    else:
        target_user = await get_user_from_db(db, target_user_id)
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")

    if avatar_request.get_default:
        encrypted = not (target_user.default_avatar or avatar_request.get_default)
    else:
        encrypted = not target_user.default_avatar

    file_name = (
        target_user.avatar_filename()
        if encrypted
        else target_user.avatar_filename_default()
    )
    s3_key: str = target_user.avatar_s3_key(file_name)
    return create_avatar_streaming_response(
        s3_client, cipher, s3_key, file_name, encrypted
    )


class AvatarVersionRequest(BaseModel):
    """Request model for getting avatar version."""

    user_id: int


@api_router_v1.post("/user/avatar/version", status_code=200, response_model=dict)
@handle_db_errors("Get user avatar version failed")
async def get_avatar_version(
    avatar_version_request: AvatarVersionRequest,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, bool | int]:
    """Handle get user detail request."""
    _, _ = user_and_token
    got_user = await get_user_from_db(db, avatar_version_request.user_id)
    if got_user is None:
        return {"success": False}

    return {"success": True, "data": got_user.avatar_version}
