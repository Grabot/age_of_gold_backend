"""Endpoint for responding to friend requests (accept/reject)."""

from typing import Dict, Tuple

from fastapi import Depends, HTTPException, Security
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models.user import User
from src.models.user_token import UserToken
from src.sockets.sockets import sio
from src.util.security import checked_auth_token
from src.util.util import get_user_room
from src.util.rest_util import get_friend_request_pair


class RespondFriendRequest(BaseModel):
    """Request model for responding to friend requests."""

    friend_id: int
    accept: bool


@api_router_v1.post("/friend/respond", status_code=200, response_model=Dict)
async def respond_friend_request(
    respond_request: RespondFriendRequest,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, bool]:
    """Handle friend request response (accept/reject)."""
    me, _ = user_and_token

    if me.id is None:
        raise HTTPException(status_code=400, detail="Can't find user")

    friend_id = respond_request.friend_id
    accept = respond_request.accept

    friend_request, reciprocal_friend = await get_friend_request_pair(
        db, me.id, friend_id
    )

    if friend_request.accepted is True:
        raise HTTPException(
            status_code=400,
            detail="Friend request already accepted",
        )

    # Only the recipient (who has accepted=False) can respond to the request
    if friend_request.accepted is None:
        raise HTTPException(
            status_code=400,
            detail="You cannot respond to a request you sent",
        )

    if accept:
        # Accept the friend request
        friend_request.accepted = True
        friend_request.friend_version += 1
        db.add(friend_request)

        reciprocal_friend.accepted = True
        reciprocal_friend.friend_version += 1
        db.add(reciprocal_friend)

        # Notify the sender that their request was accepted
        sender_room = get_user_room(friend_id)
        await sio.emit(
            "friend_request_accepted",
            {
                "friend_id": me.id,
                "username": me.username,
                "avatar_version": me.avatar_version,
                "profile_version": me.profile_version,
                "accepted": True,
                "friend_version": friend_request.friend_version,
            },
            room=sender_room,
        )
    else:
        # Reject the friend request - remove both entries
        await db.delete(friend_request)
        await db.delete(reciprocal_friend)

        # Notify the sender that their request was rejected
        sender_room = get_user_room(friend_id)
        await sio.emit(
            "friend_request_rejected",
            {
                "friend_id": me.id,
            },
            room=sender_room,
        )

    await db.commit()

    return {
        "success": True,
    }
