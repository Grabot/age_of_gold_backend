"""Endpoint for creating a group."""

from typing import Dict, List, Tuple

from fastapi import Depends, HTTPException, Security, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Select
from sqlmodel import select

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models.chat import Chat
from src.models.friend import Friend
from src.models.group import Group
from src.models.user import User
from src.models.user_token import UserToken
from src.sockets.sockets import sio
from src.util.security import checked_auth_token
from src.util.util import get_user_room

class CreateGroupRequest(BaseModel):
    """Request model for creating a group."""

    group_name: str
    group_description: str
    group_colour: str
    friend_ids: List[int]

@api_router_v1.post("/group/create", status_code=200)
async def create_group(
    create_group_request: CreateGroupRequest,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, bool | int]:
    """Handle create group request."""
    me, _ = user_and_token
    print(f"User: {me}")

    if me.id is None:
        raise HTTPException(status_code=400, detail="Can't find user")

    # Validate that all friend_ids are actual friends
    user_id = me.id
    friend_ids = [user_id] + create_group_request.friend_ids
    print(f"Friend IDs: {friend_ids}")

    # Check if all friend_ids are valid friends
    for friend_id in create_group_request.friend_ids:
        if friend_id == user_id:
            continue  # Skip self

        # Check if this is a valid friend relationship
        friend_statement: Select = select(Friend).where(
            Friend.user_id == user_id,
            Friend.friend_id == friend_id,
            Friend.accepted,
        )
        friend_result = await db.execute(friend_statement)
        friend_exists = friend_result.first()
        print(f"Friend Exists: {friend_exists}")

        if not friend_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User {friend_id} is not your friend",
            )
        friend_result = await db.execute(friend_statement)
        friend_exists = friend_result.first()
        print(f"Friend Exists: {friend_exists}")

        if not friend_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User {friend_id} is not your friend",
            )

    # Create the chat object
    new_chat = Chat(
        user_ids=friend_ids,
        user_admin_ids=[user_id],  # Creator is admin
        private=False,  # Groups are not private
        group_name=create_group_request.group_name,
        group_description=create_group_request.group_description,
        group_colour=create_group_request.group_colour,
        default_avatar=True,
        current_message_id=1,
        last_message_read_id_chat=1,
    )
    print(f"New Chat: {new_chat}")

    db.add(new_chat)
    await db.commit()
    await db.refresh(new_chat)

    # Create group entries for each user
    for friend_id in friend_ids:
        group_entry = Group(
            user_id=friend_id,
            group_id=new_chat.id,
            unread_messages=0,
            mute=False,
            group_version=1,
            message_version=1,
            avatar_version=1,
            last_message_read_id=0,
        )
        db.add(group_entry)
        print(f"Group Entry: {group_entry}")

    await db.commit()

    # Notify all group members about the new group
    for friend_id in friend_ids:
        if friend_id != user_id:  # Don't notify self
            recipient_room: str = get_user_room(friend_id)
            print(f"Recipient Room: {recipient_room}")
            await sio.emit(
                "group_created",
                {
                    "group_id": new_chat.id,
                    "group_name": new_chat.group_name,
                    "group_description": new_chat.group_description,
                    "group_colour": new_chat.group_colour,
                    "creator_id": user_id,
                    "creator_username": me.username,
                },
                room=recipient_room,
            )
    print(f"sending data: {new_chat.id}")
    return {
        "success": True,
        "data": new_chat.id
    }

