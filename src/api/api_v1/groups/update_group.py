"""Endpoint for updating group details."""

from typing import Dict, Tuple

from fastapi import Depends, HTTPException, Security, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models.chat import Chat
from src.models.user import User
from src.models.user_token import UserToken
from src.sockets.sockets import sio
from src.util.security import checked_auth_token
from src.util.util import get_user_room


class UpdateGroupRequest(BaseModel):
    """Request model for updating group details."""

    group_id: int
    group_name: str | None = None
    group_description: str | None = None
    group_colour: str | None = None


@api_router_v1.post("/group/update", status_code=200)
async def update_group(
    update_group_request: UpdateGroupRequest,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, bool]:
    """Handle update group request."""
    me, _ = user_and_token

    if me.id is None:
        raise HTTPException(status_code=400, detail="Can't find user")

    group_id = update_group_request.group_id

    # Check if the current user is an admin of the group
    chat_statement = select(Chat).where(Chat.id == group_id)
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
            detail="Only group admins can update group details",
        )

    # Update group details if provided
    if update_group_request.group_name is not None:
        chat.group_name = update_group_request.group_name
    if update_group_request.group_description is not None:
        chat.group_description = update_group_request.group_description
    if update_group_request.group_colour is not None:
        chat.group_colour = update_group_request.group_colour

    await db.commit()

    # Notify all group members about the group update
    for user_id in chat.user_ids:
        if user_id != me.id:
            recipient_room: str = get_user_room(user_id)
            await sio.emit(
                "group_updated",
                {
                    "group_id": group_id,
                    "group_name": chat.group_name,
                    "group_description": chat.group_description,
                    "group_colour": chat.group_colour,
                },
                room=recipient_room,
            )

    return {
        "success": True,
    }
