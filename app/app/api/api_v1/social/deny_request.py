from typing import Optional

from fastapi import Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.api_v1 import api_router_v1
from app.api.rest_util import get_failed_response
from app.database import get_db
from app.models import Friend, User
from app.sockets.sockets import sio
from app.util.util import check_token, get_auth_token


class DenyRequest(BaseModel):
    user_id: int


@api_router_v1.post("/deny/request", status_code=200)
async def deny_friend(
    deny_request: DenyRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    print(f"deny friend request with {deny_request.user_id}")
    auth_token = get_auth_token(request.headers.get("Authorization"))

    if auth_token == "":
        return get_failed_response("An error occurred", response)

    user_from: Optional[User] = await check_token(db, auth_token)
    if not user_from:
        return get_failed_response("An error occurred", response)

    user_id = deny_request.user_id
    user_statement = select(User).where(User.id == user_id)
    results = await db.execute(user_statement)
    result = results.first()

    if not result:
        return get_failed_response("an error occurred", response)
    user_denied: User = result.User

    statement_deny_from = select(Friend).filter_by(user_id=user_from.id, friend_id=user_denied.id)
    statement_deny_befriend = select(Friend).filter_by(
        user_id=user_denied.id, friend_id=user_from.id
    )

    results_deny_from = await db.execute(statement_deny_from)
    results_deny_befriend = await db.execute(statement_deny_befriend)

    result_deny_from = results_deny_from.first()
    result_deny_befriend = results_deny_befriend.first()

    if not result_deny_from or not result_deny_befriend:
        # They both have to exist if you're accepting one
        return get_failed_response("something went wrong", response)
    else:
        friend_from: Friend = result_deny_from.Friend
        friend_befriend: Friend = result_deny_befriend.Friend

        friend_from.requested = None
        friend_befriend.requested = None

        if friend_from.accepted:
            # We also set the accepted back to false.
            # This can be a denied request or an unfriend.
            friend_from.accepted = False
            friend_befriend.accepted = False
            # TODO: Add message that they are unfriended?
        db.add(friend_from)
        db.add(friend_befriend)
        await db.commit()

        socket_response = {
            "friend_id": user_from.id,
        }
        room_to = "room_%s" % user_denied.id
        await sio.emit(
            "denied_friend",
            socket_response,
            room=room_to,
        )

        return {"result": True, "message": "success"}
