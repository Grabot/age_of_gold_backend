"""Endpoint for adding a friend."""

from typing import Tuple

from fastapi import Depends, HTTPException, Security, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.sql.selectable import Select
from sqlmodel import select

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models import Friend, Chat, User, UserToken
from src.util.decorators import handle_db_errors
from src.util.security import checked_auth_token
from src.util.util import get_user_room
from src.util.rest_util import emit_friend_response


class AddFriendRequest(BaseModel):
    """Request model for adding a friend."""

    user_id: int


@api_router_v1.post("/friend/add", status_code=200)
@handle_db_errors(default_error_message="No user found.")
async def add_friend(
    add_friend_request: AddFriendRequest,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool | int]:
    """Handle add friend request."""
    me, _ = user_and_token

    print(f"Add friend request received for user_id: {add_friend_request.user_id}")

    friend_id = add_friend_request.user_id
    if friend_id is me.id:
        print("User tried to add themselves as a friend")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can't add yourself",
        )

    print(f"Checking if user with id {friend_id} exists")
    friend_statement: Select = select(User).where(User.id == friend_id)
    friend_add: User = (await db.execute(friend_statement)).scalar_one()

    print(f"Checking if user with id {me.id} is already friends with user with id {friend_add.id}")
    existing_friend_statement: Select = select(Friend).where(
        Friend.user_id == me.id, Friend.friend_id == friend_add.id
    )
    existing_friend_result = await db.execute(existing_friend_statement)
    existing_friend = existing_friend_result.first()

    if existing_friend:
        print("Users are already friends")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already friends",
        )

    print("Creating a new chat for the users")
    user_ids = [me.id, friend_id]
    user_ids.sort()
    new_chat = Chat(
        user_ids=user_ids,
        user_admin_ids=user_ids,
        private=True,
        name=None,
        description=None,
        colour=None,
        default_avatar=True,
        current_message_id=1,
        last_message_read_id_chat=1,
    )
    db.add(new_chat)
    await db.commit()
    await db.refresh(new_chat)
    print(f"friend accepted, chat created {new_chat.id}")

    print("Creating friend entries for both users")
    friend_me = Friend(
        user_id=me.id, # pyright: ignore[reportArgumentType]
        friend_id=friend_add.id, # pyright: ignore[reportArgumentType]
        accepted=None,
        chat_id=new_chat.id
    )
    friend_other = Friend(
        user_id=friend_add.id, # pyright: ignore[reportArgumentType]
        friend_id=me.id, # pyright: ignore[reportArgumentType]
        accepted=False,
        chat_id=new_chat.id
    )

    db.add(friend_me)
    db.add(friend_other)
    await db.commit()

    print(f"Emitting friend request to user with id {friend_add.id}")
    recipient_room: str = get_user_room(friend_add.id)  # type: ignore[arg-type]
    await emit_friend_response("friend_request_received", me, recipient_room, new_chat.id)

    print("Friend request processed successfully")
    return {
        "success": True,
        "data": new_chat.id
    }
