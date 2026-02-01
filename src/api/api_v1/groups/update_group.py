"""Endpoint for updating group details."""

from typing import Dict, Tuple

from fastapi import Depends, HTTPException, Security, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models.chat import Chat
from src.models.user import User
from src.models.user_token import UserToken
from src.sockets.sockets import sio
from src.util.security import checked_auth_token
from src.util.util import get_group_room


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

    chat_statement = (
        select(Chat).where(Chat.id == group_id).options(selectinload(Chat.groups))
    )
    # TODO: Change scalar().first() to scalar_one where we expect there to always be a result
    # TODO: Maybe add `NoResultFound` in the `handle_db_error` wrapper
    chat: Chat = (await db.execute(chat_statement)).scalar_one()

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
    db.add(chat)

    for group in chat.groups:
        group.group_version += 1
        db.add(group)

    await db.commit()

    # TODO: Only send what is changed?
    group_room: str = get_group_room(group_id)
    await sio.emit(
        "group_updated",
        {
            "group_id": group_id,
            "group_name": chat.group_name,
            "group_description": chat.group_description,
            "group_colour": chat.group_colour,
        },
        room=group_room,
    )

    return {
        "success": True,
    }
