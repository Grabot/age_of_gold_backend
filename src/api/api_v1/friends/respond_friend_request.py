"""Endpoint for responding to friend requests (accept/reject)."""

from typing import Any, Dict, Tuple

from fastapi import Depends, HTTPException, Security
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Select
from sqlmodel import select

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models import Chat, User, UserToken
from src.sockets.sockets import sio
from src.util.decorators import handle_db_errors
from src.util.rest_util import emit_friend_response, get_friend_request_pair
from src.util.security import checked_auth_token
from src.util.util import get_user_room


class RespondFriendRequest(BaseModel):
    """Request model for responding to friend requests."""

    friend_id: int
    chat_id: int
    accept: bool


@api_router_v1.post("/friend/respond", status_code=200, response_model=Dict)
@handle_db_errors("Responding to request failed")
async def respond_friend_request(
    respond_request: RespondFriendRequest,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Handle friend request response (accept/reject)."""
    me, _ = user_and_token

    friend_id = respond_request.friend_id
    chat_id = respond_request.chat_id
    accept = respond_request.accept

    friend_request, reciprocal_friend = await get_friend_request_pair(
        db,
        me.id,  # type: ignore[arg-type]
        friend_id,
        chat_id
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
        await emit_friend_response(
            "friend_request_accepted",
            me,
            sender_room,
            reciprocal_friend.chat_id,
            additional_data={
                "accepted": True,
                "friend_version": friend_request.friend_version,
            },
        )

        await db.commit()

        return {
            "success": True,
        }

    else:
        # Reject the friend request - remove both entries and the chat.
        chat_statement: Select = select(Chat).where(Chat.id == chat_id)
        chat: Chat = (await db.execute(chat_statement)).scalar_one()
        await db.delete(friend_request)
        await db.delete(reciprocal_friend)
        await db.delete(chat)

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
