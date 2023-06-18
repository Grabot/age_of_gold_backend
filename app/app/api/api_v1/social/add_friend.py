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


class AddFriendRequest(BaseModel):
    user_id: int


@api_router_v1.post("/add/friend", status_code=200)
async def add_friend(
    add_friend_request: AddFriendRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    print(f"accept friend request with {add_friend_request.user_id}")
    auth_token = get_auth_token(request.headers.get("Authorization"))

    if auth_token == "":
        get_failed_response("An error occurred", response)

    user_from: Optional[User] = await check_token(db, auth_token)
    if not user_from:
        get_failed_response("An error occurred", response)

    user_id = add_friend_request.user_id
    user_statement = select(User).where(User.id == user_id)
    results = await db.execute(user_statement)
    result = results.first()

    if not result:
        return get_failed_response("an error occurred", response)
    user_befriend: User = result.User

    statement_friend_from = select(Friend).filter_by(
        user_id=user_from.id, friend_id=user_befriend.id
    )

    results_friend_from = await db.execute(statement_friend_from)

    result_friend_from = results_friend_from.first()

    if not result_friend_from:
        print("they were not friends yet, so going to create the friend objects")
        # not friends yet, create Friend objects, always for both users!
        friend_befriend = user_befriend.befriend(user_from)
        friend_from = user_from.befriend(user_befriend)
    else:
        statement_friend_befriend = select(Friend).filter_by(
            user_id=user_befriend.id, friend_id=user_from.id
        )
        results_friend_befriend = await db.execute(statement_friend_befriend)
        result_friend_befriend = results_friend_befriend.first()

        # if one of the objects exists the other should exist too.
        if not result_friend_befriend:
            return get_failed_response("an error occurred", response)
        friend_from: Friend = result_friend_from.Friend
        friend_befriend: Friend = result_friend_befriend.Friend

    # set requested indicator
    if friend_from.requested is True and friend_befriend.requested is False:
        print("request is already sent!")
        return {"result": True, "message": "request already sent"}
    elif friend_befriend.requested is True and friend_from.requested is False:
        print("The other person has sent a request")
        # This is if a friend request is send by the other person and now this person sends one
        # Let's assume they both accept to be friends
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

        return {"result": True, "message": "They are now friends"}
    else:
        print("Successfully sent a request")
        friend_from.requested = True
        friend_befriend.requested = False
        db.add(friend_from)
        db.add(friend_befriend)
        await db.commit()
        # Emit on the room of the person. If that person is online they will see the request
        socket_response = {
            "from": user_from.serialize_minimal,
        }
        room_to = "room_%s" % user_befriend.id
        await sio.emit(
            "received_friend_request",
            socket_response,
            room=room_to,
        )

        return {"result": True, "message": "success"}
