"""Endpoint for promoting/demoting a user to/from admin in a group."""

from typing import Dict, Tuple

from fastapi import Depends, HTTPException, Security, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy.sql.selectable import Select
from sqlalchemy.orm import selectinload

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models import Group, Chat, User
from src.models.user_token import UserToken
from src.sockets.sockets import sio
from src.util.security import checked_auth_token
from src.util.util import get_user_room


class PromoteAdminRequest(BaseModel):
    """Request model for promoting/demoting a user to/from admin."""

    group_id: int
    user_id: int
    is_admin: bool


@api_router_v1.post("/group/admin/promote", status_code=200)
async def promote_admin(
    promote_admin_request: PromoteAdminRequest,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, bool]:
    """Handle promote/demote admin request."""
    me, _ = user_and_token

    if me.id is None:
        raise HTTPException(status_code=400, detail="Can't find user")

    group_id = promote_admin_request.group_id
    target_user_id = promote_admin_request.user_id
    is_admin = promote_admin_request.is_admin

    # Check if the current user is an admin of the group
    chat_statement = select(Chat).where(Chat.id == group_id).options(selectinload(Chat.groups))
    chat_result = await db.execute(chat_statement)
    chat_entry = chat_result.first()

    if not chat_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    chat: Chat = chat_entry.Chat

    # Check if current user is admin
    if me.id not in chat.user_admin_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only group admins can change admin status",
        )

    # Check if the target user is in the group
    if target_user_id not in chat.user_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not in the group",
        )

    # Update admin status
    if is_admin:
        # Promote to admin
        if target_user_id not in chat.user_admin_ids:
            chat.add_admin(target_user_id)
    else:
        # Demote from admin
        if target_user_id in chat.user_admin_ids:
            chat.remove_admin(target_user_id)

    db.add(chat)

    for group in chat.groups:
        group.group_version += 1
        db.add(group)
    await db.commit()

    # Notify all group members about the admin change
    for group in chat.groups:
        recipient_room: str = get_user_room(group.user_id)
        if group.user_id != me.id:
            await sio.emit(
                "group_admin_changed",
                {
                    "group_id": group_id,
                    "user_id": target_user_id,
                    "is_admin": is_admin,
                },
                room=recipient_room,
            )

    return {
        "success": True,
    }
