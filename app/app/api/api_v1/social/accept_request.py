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


class AcceptRequest(BaseModel):
    user_id: int


@api_router_v1.post("/accept/request", status_code=200)
async def accept_friend(
    accept_request: AcceptRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    print(f"accept friend request with {accept_request.user_id}")
    auth_token = get_auth_token(request.headers.get("Authorization"))

    if auth_token == "":
        return get_failed_response("An error occurred", response)

    user_from: Optional[User] = await check_token(db, auth_token)
    if not user_from:
        return get_failed_response("An error occurred", response)

    user_id = accept_request.user_id
    user_statement = select(User).where(User.id == user_id)
    results = await db.execute(user_statement)
    result = results.first()

    if not result:
        return get_failed_response("an error occurred", response)
    user_befriend: User = result.User

    statement_friend_from = select(Friend).filter_by(
        user_id=user_from.id, friend_id=user_befriend.id
    )
    statement_friend_befriend = select(Friend).filter_by(
        user_id=user_befriend.id, friend_id=user_from.id
    )

    results_friend_from = await db.execute(statement_friend_from)
    results_friend_befriend = await db.execute(statement_friend_befriend)

    result_friend_from = results_friend_from.first()
    result_friend_befriend = results_friend_befriend.first()

    if not result_friend_from or not result_friend_befriend:
        # They both have to exist if you're accepting one
        return get_failed_response("something went wrong", response)

    friend_from: Friend = result_friend_from.Friend
    friend_befriend: Friend = result_friend_befriend.Friend

    friend_from.accepted = True
    friend_befriend.accepted = True
    db.add(friend_from)
    db.add(friend_befriend)
    await db.commit()

    socket_response = {
        "from": user_from.serialize_minimal,
    }
    room_to = "room_%s" % user_befriend.id
    await sio.emit(
        "accept_friend_request",
        socket_response,
        room=room_to,
    )

    return {"result": True, "message": "success"}
