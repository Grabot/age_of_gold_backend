"""Endpoint for leaving a group."""

from typing import Dict, Tuple

from fastapi import Depends, HTTPException, Security
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
from src.util.util import get_user_room


class LeaveGroupRequest(BaseModel):
    """Request model for leaving a group."""

    group_id: int


@api_router_v1.post("/group/leave", status_code=200)
@handle_db_errors("Leaving group failed")
async def leave_group(
    leave_group_request: LeaveGroupRequest,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, bool]:
    """Handle leave group request."""
    me, _ = user_and_token

    group_id = leave_group_request.group_id

    # Get the group entry for this user
    group_statement: Select = select(Group).where(
        Group.user_id == me.id, Group.group_id == group_id
    )
    group_result = await db.execute(group_statement)
    group_entry = group_result.first()

    if not group_entry:
        raise HTTPException(
            status_code=404,
            detail="Group not found",
        )

    chat_statement: Select = select(Chat).where(Chat.id == group_id)
    chat: Chat = (await db.execute(chat_statement)).scalar_one()

    # Remove user from admin list if they are an admin
    if me.id in chat.user_admin_ids:
        chat.user_admin_ids = [
            admin_id for admin_id in chat.user_admin_ids if admin_id != me.id
        ]

    # Remove user from user list
    chat.user_ids = [user_id for user_id in chat.user_ids if user_id != me.id]

    # Delete the group entry for this user
    await db.delete(group_entry.Group)

    # If this was the last user in the group, delete the chat too
    if len(chat.user_ids) == 0:
        await db.delete(chat)

    await db.commit()

    # Notify other group members that someone left
    for user_id in chat.user_ids:
        recipient_room: str = get_user_room(user_id)
        await sio.emit(
            "group_member_left",
            {
                "group_id": group_id,
                "user_id": me.id,
            },
            room=recipient_room,
        )

    return {
        "success": True,
    }
