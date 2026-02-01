"""Endpoint for adding a member to a group."""

from typing import Dict, Tuple

from fastapi import Depends, HTTPException, Security, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models.group import Group
from src.models.user import User
from src.models.user_token import UserToken
from src.util.decorators import handle_db_errors
from src.util.security import checked_auth_token
from src.util.util import (
    get_user_room,
    get_chat_and_verify_admin,
)
from src.util.rest_util import update_group_versions_and_notify, emit_group_response


class AddGroupMemberRequest(BaseModel):
    """Request model for adding a member to a group."""

    group_id: int
    user_add_id: int


@api_router_v1.post("/group/member/add", status_code=200)
@handle_db_errors("Adding group member failed")
async def add_group_member(
    add_group_member_request: AddGroupMemberRequest,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, bool]:
    """Handle add group member request."""
    me, _ = user_and_token

    group_id = add_group_member_request.group_id
    new_user_id = add_group_member_request.user_add_id

    # Check if the current user is an admin of the group
    chat = await get_chat_and_verify_admin(
        db, group_id, me.id, permission_error_detail="Only group admins can add members"
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
        last_message_read_id=0,
    )
    db.add(group_entry)

    await db.commit()

    # Notify other group members about the new member
    await update_group_versions_and_notify(
        chat,
        db,
        me,
        "group_member_added",
        {
            "group_id": group_id,
            "user_id": new_user_id,
        },
    )

    # Notify the new member about the group
    new_member_room: str = get_user_room(new_user_id)
    await emit_group_response(
        "group_created",
        chat,
        new_member_room,
        {
            "user_ids": chat.user_ids,
            "admin_ids": chat.user_admin_ids,
            "private": chat.private,
            "current_message_id": chat.current_message_id,
        },
    )

    return {
        "success": True,
    }
