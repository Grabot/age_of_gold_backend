from fastapi import Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.api_v1 import api_router_v1
from app.api.rest_util import get_failed_response
from app.database import get_db
from app.models import Friend, User
from app.util.util import check_token, get_auth_token


class ReadMessagePersonalRequest(BaseModel):
    user_read_id: int


@api_router_v1.post("/read/message/personal", status_code=200)
async def read_personal_message(
    request: Request,
    read_message_personal_request: ReadMessagePersonalRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    auth_token = get_auth_token(request.headers.get("Authorization"))
    if auth_token == "":
        return get_failed_response("an error occurred", response)

    user_request = await check_token(db, auth_token)
    if not user_request:
        return get_failed_response("an error occurred", response)

    read_user_id = read_message_personal_request.user_read_id

    statement_user_read = select(User).where(User.id == read_user_id)
    user_read_results = await db.execute(statement_user_read)
    user_read_result = user_read_results.first()
    if not user_read_result:
        return get_failed_response("user not found", response)

    user_read: User = user_read_result.User

    statement_friend_read = select(Friend).filter_by(
        user_id=user_request.id, friend_id=user_read.id
    )
    friend_read_results = await db.execute(statement_friend_read)
    friend_read_result = friend_read_results.first()

    if not friend_read_result:
        return get_failed_response("user not found", response)

    friend: Friend = friend_read_result.Friend

    print("unread messages: %s" % friend.unread_messages)

    friend.read_messages()
    db.add(friend)
    await db.commit()

    return {"result": True, "message": "success"}
