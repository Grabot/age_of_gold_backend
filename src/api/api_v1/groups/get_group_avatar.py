"""Endpoint for getting user avatar."""

from typing import Dict, Tuple, Any, Optional
from pydantic import BaseModel

from fastapi import Depends, HTTPException, Security, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models import User, UserToken, Group, Chat
from src.util.decorators import handle_db_errors
from src.util.security import checked_auth_token
from src.util.util import create_avatar_streaming_response


class GroupAvatarRequest(BaseModel):
    """Request model for getting group avatar."""

    group_id: int
    get_default: Optional[bool] = None


@api_router_v1.post("/group/avatar", status_code=200)
@handle_db_errors("Get group avatar failed")
async def get_group_avatar(
    request: Request,
    group_avatar_request: GroupAvatarRequest,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Handle get group avatar request for a group by group ID."""
    user, _ = user_and_token
    s3_client: Any = request.app.state.s3
    cipher: Any = request.app.state.cipher

    target_group_id = group_avatar_request.group_id
    groups_statement = (
        select(Group)
        .where(Group.user_id == user.id, Group.group_id == target_group_id)
        .options(selectinload(Group.chat))
    )
    group_result = await db.execute(groups_statement)
    group_entry = group_result.first()

    if not group_entry or not group_entry.Group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )
    target_group: Group = group_entry.Group

    if group_avatar_request.get_default:
        encrypted = not (
            target_group.chat.default_avatar or group_avatar_request.get_default
        )
    else:
        encrypted = not target_group.chat.default_avatar

    file_name = (
        target_group.chat.group_avatar_filename()
        if encrypted
        else target_group.chat.group_avatar_filename_default()
    )
    s3_key: str = target_group.chat.group_avatar_s3_key(file_name)
    return create_avatar_streaming_response(
        s3_client, cipher, s3_key, file_name, encrypted
    )


class GroupAvatarVersionRequest(BaseModel):
    """Request model for getting avatar version."""

    group_id: int


@api_router_v1.post("/group/avatar/version", status_code=200, response_model=dict)
@handle_db_errors("Get group avatar version failed")
async def get_group_avatar_version(
    group_avatar_version_request: GroupAvatarVersionRequest,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, bool | int]:
    """Handle get group avatar version request."""
    _, _ = user_and_token
    got_chat = await db.get(Chat, group_avatar_version_request.group_id)
    if got_chat is None:
        return {"success": False}

    return {"success": True, "data": got_chat.avatar_version}
