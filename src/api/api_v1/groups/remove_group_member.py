"""Endpoint for removing a member from a group."""

from typing import Dict, Tuple

from fastapi import Depends, HTTPException, Security, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Select
from sqlmodel import select

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models.chat import Chat
from src.models.group import Group
from src.models.user import User
from src.models.user_token import UserToken
from src.sockets.sockets import sio
from src.util.decorators import handle_db_errors
from src.util.security import checked_auth_token
from src.util.util import get_group_room


class RemoveGroupMemberRequest(BaseModel):
    """Request model for removing a member from a group."""

    chat_id: int
    user_remove_id: int


@api_router_v1.post("/group/member/remove", status_code=200)
@handle_db_errors("Remove group member failed")
async def remove_group_member(
    remove_group_member_request: RemoveGroupMemberRequest,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, bool]:
    """Handle remove group member request."""
    me, _ = user_and_token

    chat_id = remove_group_member_request.chat_id
    user_to_remove_id = remove_group_member_request.user_remove_id

    # Check if the current user is an admin of the group or is removing themselves
    chat_statement: Select = select(Chat).where(Chat.id == chat_id)
    chat_result = await db.execute(chat_statement)
    chat_entry = chat_result.first()

    if not chat_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    chat: Chat = chat_entry.Chat

    # Check if current user is admin or is removing themselves
    if me.id not in chat.user_admin_ids and me.id != user_to_remove_id:
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

    # Remove user from user list and delete the group entry for this user
    chat.user_ids = [
        user_id for user_id in chat.user_ids if user_id != user_to_remove_id
    ]

    group_statement: Select = select(Group).where(
        Group.user_id == user_to_remove_id, Group.chat_id == chat_id
    )
    group_result = await db.execute(group_statement)
    group_entry = group_result.first()

    if group_entry:
        await db.delete(group_entry.Group)

    await db.commit()

    group_room = get_group_room(chat_id)
    await sio.emit(
        "group_member_removed",
        {
            "chat_id": chat_id,
            "user_id": user_to_remove_id,
        },
        room=group_room,
    )

    return {
        "success": True,
    }
