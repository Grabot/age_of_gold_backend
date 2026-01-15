"""Endpoint for adding a member to a group."""

from typing import Dict, Tuple

from fastapi import Depends, HTTPException, Security, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy.orm import selectinload

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models.chat import Chat
from src.models.group import Group
from src.models.user import User
from src.models.user_token import UserToken
from src.sockets.sockets import sio
from src.util.security import checked_auth_token
from src.util.util import get_user_room


class AddGroupMemberRequest(BaseModel):
    """Request model for adding a member to a group."""

    group_id: int
    user_id: int


@api_router_v1.post("/group/member/add", status_code=200)
async def add_group_member(
    add_group_member_request: AddGroupMemberRequest,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, bool]:
    """Handle add group member request."""
    me, _ = user_and_token

    if me.id is None:
        raise HTTPException(status_code=400, detail="Can't find user")

    group_id = add_group_member_request.group_id
    new_user_id = add_group_member_request.user_id

    # Check if the current user is an admin of the group
    chat_statement = (
        select(Chat).where(Chat.id == group_id).options(selectinload(Chat.groups))
    )
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
            detail="Only group admins can add members",
        )

    # Check if the user to add is already in the group
    if new_user_id in chat.user_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already in the group",
        )

    # For non-private groups, check if the user to add is a friend of at least one admin
    # For now, we'll skip this check and allow any user to be added

    # Add user to the chat
    chat.add_user(new_user_id)
    db.add(chat)

    # Create a group entry for the new user
    group_entry = Group(
        user_id=new_user_id,
        group_id=group_id,
        unread_messages=0,
        mute=False,
        group_version=1,
        message_version=1,
        avatar_version=1,
        last_message_read_id=0,
    )
    db.add(group_entry)

    await db.commit()

    # Notify other group members about the new member
    for group in chat.groups:
        group.group_version += 1
        db.add(group)
    await db.commit()

    # Notify other group members about the new member
    for group in chat.groups:
        recipient_room: str = get_user_room(group.user_id)
        if group.user_id != me.id:
            await sio.emit(
                "group_member_added",
                {
                    "group_id": group_id,
                    "user_id": new_user_id,
                },
                room=recipient_room,
            )

    # Notify the new member about the group
    new_member_room: str = get_user_room(new_user_id)
    await sio.emit(
        "group_created",
        {
            "group_id": chat.id,
            "user_ids": chat.user_ids,
            "admin_ids": chat.user_admin_ids,
            "group_name": chat.group_name,
            "private": chat.private,
            "group_description": chat.group_description,
            "group_colour": chat.group_colour,
            "current_message_id": chat.current_message_id
        },
        room=new_member_room,
    )

    return {
        "success": True,
    }
