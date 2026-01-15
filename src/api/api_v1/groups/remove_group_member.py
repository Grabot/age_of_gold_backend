"""Endpoint for removing a member from a group."""

from typing import Dict, Tuple

from fastapi import Depends, HTTPException, Security, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models.chat import Chat
from src.models.group import Group
from src.models.user import User
from src.models.user_token import UserToken
from src.sockets.sockets import sio
from src.util.security import checked_auth_token
from src.util.util import get_user_room


class RemoveGroupMemberRequest(BaseModel):
    """Request model for removing a member from a group."""

    group_id: int
    user_id: int


@api_router_v1.post("/group/member/remove", status_code=200)
async def remove_group_member(
    remove_group_member_request: RemoveGroupMemberRequest,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, bool]:
    """Handle remove group member request."""
    me, _ = user_and_token

    if me.id is None:
        raise HTTPException(status_code=400, detail="Can't find user")

    group_id = remove_group_member_request.group_id
    user_to_remove_id = remove_group_member_request.user_id

    # Check if the current user is an admin of the group or is removing themselves
    chat_statement = select(Chat).where(Chat.id == group_id)
    chat_result = await db.execute(chat_statement)
    chat_entry = chat_result.first()

    if not chat_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    chat: Chat = chat_entry.Chat

    # Check if current user is admin or is removing themselves
    is_admin = me.id in chat.user_admin_ids
    is_self = me.id == user_to_remove_id

    if not is_admin and not is_self:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only group admins can remove members",
        )

    # Check if the user to remove is in the group
    if user_to_remove_id not in chat.user_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not in the group",
        )

    # Remove user from admin list if they are an admin
    if user_to_remove_id in chat.user_admin_ids:
        chat.user_admin_ids = [
            admin_id
            for admin_id in chat.user_admin_ids
            if admin_id != user_to_remove_id
        ]

    # Remove user from user list
    chat.user_ids = [
        user_id for user_id in chat.user_ids if user_id != user_to_remove_id
    ]

    # Delete the group entry for this user
    group_statement = select(Group).where(
        Group.user_id == user_to_remove_id, Group.group_id == group_id
    )
    group_result = await db.execute(group_statement)
    group_entry = group_result.first()

    if group_entry:
        await db.delete(group_entry.Group)

    await db.commit()

    # Notify other group members that someone was removed
    for user_id in chat.user_ids:
        if user_id != me.id:
            recipient_room: str = get_user_room(user_id)
            await sio.emit(
                "group_member_removed",
                {
                    "group_id": group_id,
                    "user_id": user_to_remove_id,
                },
                room=recipient_room,
            )

    return {
        "success": True,
    }
