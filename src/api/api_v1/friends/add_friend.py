"""Endpoint for adding a friend."""

from typing import Tuple

from fastapi import Depends, HTTPException, status, Security
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
import random

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models.chat import Chat
from src.models.group import Group
from src.models.user import User
from src.models.user_token import UserToken
from src.util.security import checked_auth_token
from src.sockets.sockets import sio

def create_group(
    user_id: int, group_id: int
) -> Group:

    group = Group(
        user_id=user_id,
        group_id=group_id,
        unread_messages=0,
        mute=False,
    )
    return group

class AddFriendRequest(BaseModel):
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

    if friend_id is me.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can't add yourself",
        )

    user_statement = select(User).where(User.id == friend_id)
    results_user = await db.execute(user_statement)
    result_user = results_user.first()

    if not result_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No user found.",
        )

    friend_add: User = result_user.User

    if me.id is None or friend_add.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No user found.",
        )

    # TODO: Add a friend object or a group object with a friend flag?
