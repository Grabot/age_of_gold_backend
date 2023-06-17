from datetime import datetime
from typing import Optional

from fastapi import Depends, Request, Response
from pydantic import BaseModel
from sockets.sockets import sio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from util.util import check_token, get_auth_token

from app.api.api_v1 import api_router_v1
from app.api.rest_util import get_failed_response
from app.database import get_db
from app.models import Friend, User
from app.models.message import PersonalMessage


class SendMessagePersonalRequest(BaseModel):
    message: str
    user_id: int


@api_router_v1.post("/send/message/personal", status_code=200)
async def send_personal_message(
    send_message_personal_request: SendMessagePersonalRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    auth_token = get_auth_token(request.headers.get("Authorization"))
    if auth_token == "":
        return get_failed_response("an error occurred", response)

    user_send: Optional[User] = await check_token(db, auth_token)
    if not user_send:
        return get_failed_response("an error occurred", response)

    message_body = send_message_personal_request.message
    user_id = send_message_personal_request.user_id

    statement_user_receive = select(User).where(User.id == user_id)
    user_receive_results = await db.execute(statement_user_receive)
    user_receive_result = user_receive_results.first()
    if not user_receive_result:
        return get_failed_response("user not found", response)
    user_receive: User = user_receive_result.User

    friend_send_statement = select(Friend).filter_by(
        user_id=user_send.id, friend_id=user_receive.id
    )
    friend_send_results = await db.execute(friend_send_statement)
    friend_send_result = friend_send_results.first()
    if not friend_send_result:
        print("no friends yet")
        friend_send = user_send.befriend(user_receive)
        friend_receive = user_receive.befriend(user_send)
        db.add(friend_receive)
        print("added friends")
    else:
        print("friend object found")
        friend_send: Friend = friend_send_result.Friend

    db.add(friend_send)

    now = datetime.utcnow()

    room_receive = "room_%s" % user_receive.id
    room_to = "room_%s" % user_send.id
    socket_response = {
        "sender_name": user_send.username,
        "sender_id": user_send.id,
        "receiver_name": user_receive.username,
        "message": message_body,
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%S.%f"),
    }

    await sio.emit(
        "send_message_personal",
        socket_response,
        room=room_receive,
    )
    await sio.emit(
        "send_message_personal",
        socket_response,
        room=room_to,
    )

    # I could add the Friend object on the message,
    # but it's not needed for storage or retrieval, so we won't
    new_personal_message = PersonalMessage(
        body=message_body,
        user_id=user_send.id,
        receiver_id=user_receive.id,
        timestamp=now,
    )

    db.add(new_personal_message)
    await db.commit()
    return {
        "result": True,
    }
