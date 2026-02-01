"""Endpoint for canceling friend requests."""

from typing import Dict, Tuple

from fastapi import Depends, HTTPException, Security
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models.user import User
from src.models.user_token import UserToken
from src.sockets.sockets import sio
from src.util.decorators import handle_db_errors
from src.util.security import checked_auth_token
from src.util.util import get_user_room
from src.util.rest_util import get_friend_request_pair


class CancelFriendRequest(BaseModel):
    """Request model for canceling friend requests."""

    friend_id: int


@api_router_v1.post("/friend/cancel", status_code=200, response_model=Dict)
@handle_db_errors("Cancel friend request failed")
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

    friend_request, reciprocal_friend = await get_friend_request_pair(
        db, me.id, friend_id
    )

    # Only the sender (who has accepted = null) can cancel the request
    if friend_request.accepted is not None:
        raise HTTPException(
            status_code=400,
            detail="You can only cancel requests you have sent",
        )

    # Remove both friend entries
    await db.delete(friend_request)
    await db.delete(reciprocal_friend)

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
