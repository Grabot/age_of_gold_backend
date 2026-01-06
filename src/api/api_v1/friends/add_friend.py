"""Endpoint for adding a friend."""

from typing import Tuple

from fastapi import Depends, HTTPException, status, Security
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models.user import User
from src.models.friend import Friend
from src.models.user_token import UserToken
from src.sockets.sockets import sio
from src.util.security import checked_auth_token
from src.util.util import get_user_room


class AddFriendRequest(BaseModel):
    """Request model for adding a friend."""

    user_id: int


@api_router_v1.post("/friend/add", status_code=200)
async def add_friend(
    add_friend_request: AddFriendRequest,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Handle add friend request."""
    me, _ = user_and_token
    friend_id = add_friend_request.user_id
    print(f"Friend ID: {friend_id}")

    if friend_id is me.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can't add yourself",
        )

    friend_statement = select(User).where(User.id == friend_id)
    results_user = await db.execute(friend_statement)
    result_user = results_user.first()
    print(f"Result User: {result_user}")

    if me.id is None or not result_user or result_user.User.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No user found.",
        )

    friend_add: User = result_user.User

    existing_friend_statement = select(Friend).where(
        Friend.user_id == me.id, Friend.friend_id == friend_add.id
    )
    existing_friend_result = await db.execute(existing_friend_statement)
    existing_friend = existing_friend_result.first()

    if existing_friend:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already friends",
        )

    friend_me = Friend(user_id=me.id, friend_id=friend_add.id, accepted=None)
    friend_other = Friend(user_id=friend_add.id, friend_id=me.id, accepted=False)
    db.add(friend_me)
    db.add(friend_other)
    await db.commit()

    recipient_room = get_user_room(friend_add.id)
    await sio.emit(
        "friend_request_received",
        {
            "friend_id": me.id,
            "username": me.username,
            "avatar_version": me.avatar_version,
            "profile_version": me.profile_version,
        },
        room=recipient_room,
    )

    return {
        "success": True,
    }
