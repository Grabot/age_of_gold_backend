"""Endpoint for removing friends."""

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


class RemoveFriendRequest(BaseModel):
    """Request model for removing friends."""

    friend_id: int


@api_router_v1.post("/friend/remove", status_code=200, response_model=Dict)
async def remove_friend(
    remove_request: RemoveFriendRequest,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, bool]:
    """Handle friend removal."""
    me, _ = user_and_token

    if me.id is None:
        raise HTTPException(status_code=400, detail="Can't find user")

    friend_id = remove_request.friend_id

    friend_request, reciprocal_friend = await get_friend_request_pair(
        db, me.id, friend_id
    )

    # Only allow removal if the friendship is accepted
    if friend_request.accepted is not True:
        raise HTTPException(
            status_code=400,
            detail="Can only remove accepted friends",
        )

    # Remove both friend entries
    await db.delete(friend_request)
    await db.delete(reciprocal_friend)

    # Notify the other user that they were removed as a friend
    other_user_room = get_user_room(friend_id)
    await sio.emit(
        "friend_removed",
        {
            "friend_id": me.id,
        },
        room=other_user_room,
    )

    await db.commit()

    return {
        "success": True,
    }
