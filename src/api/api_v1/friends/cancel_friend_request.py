"""Endpoint for canceling friend requests."""

from typing import Dict, Tuple

from fastapi import Depends, HTTPException, Security
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models.friend import Friend
from src.models.user import User
from src.models.user_token import UserToken
from src.sockets.sockets import sio
from src.util.security import checked_auth_token
from src.util.util import get_user_room
from sqlmodel import select


class CancelFriendRequest(BaseModel):
    """Request model for canceling friend requests."""

    friend_id: int


@api_router_v1.post("/friend/cancel", status_code=200, response_model=Dict)
async def cancel_friend_request(
    cancel_request: CancelFriendRequest,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, bool]:
    """Handle friend request cancellation."""
    me, _ = user_and_token
    friend_id = cancel_request.friend_id

    # Find the friend request from the sender's perspective (should have accepted = null)
    friend_request_statement = select(Friend).where(
        Friend.user_id == me.id, Friend.friend_id == friend_id
    )
    friend_request_result = await db.execute(friend_request_statement)
    friend_request = friend_request_result.first()

    if not friend_request:
        raise HTTPException(
            status_code=404,
            detail="Friend request not found",
        )

    # Only the sender (who has accepted = null) can cancel the request
    if friend_request.Friend.accepted is not None:
        raise HTTPException(
            status_code=400,
            detail="You can only cancel requests you have sent",
        )

    # Remove both friend entries
    await db.delete(friend_request.Friend)

    # Also remove the reciprocal friend entry
    reciprocal_friend_statement = select(Friend).where(
        Friend.user_id == friend_id, Friend.friend_id == me.id
    )
    reciprocal_friend_result = await db.execute(reciprocal_friend_statement)
    reciprocal_friend = reciprocal_friend_result.first()

    if reciprocal_friend:
        await db.delete(reciprocal_friend.Friend)

    # Notify the recipient that the request was canceled
    recipient_room = get_user_room(friend_id)
    await sio.emit(
        "friend_request_canceled",
        {
            "friend_id": me.id,
        },
        room=recipient_room,
    )

    await db.commit()

    return {
        "success": True,
    }
