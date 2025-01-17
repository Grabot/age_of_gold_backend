from datetime import datetime
from typing import Optional

from fastapi import Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.api_v1 import api_router_v1
from app.util.rest_util import get_failed_response
from app.database import get_db
from app.models import User
from app.models.message import GlobalMessage
from app.sockets.sockets import sio
from app.util.util import check_token, get_auth_token
import pytz


class SendMessageGlobalRequest(BaseModel):
    message: str


@api_router_v1.post("/send/message/global", status_code=200)
async def send_global_message(
    send_message_global_request: SendMessageGlobalRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    auth_token = get_auth_token(request.headers.get("Authorization"))
    if auth_token == "":
        return get_failed_response("an error occurred", response)

    user: Optional[User] = await check_token(db, auth_token)
    if not user:
        return get_failed_response("an error occurred", response)

    message_body = send_message_global_request.message
    users_username = user.username
    users_id = user.id

    now = datetime.now(pytz.utc).replace(tzinfo=None)

    socket_response = {
        "body": message_body,
        "sender_name": users_username,
        "sender_id": users_id,
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%S.%f"),
    }

    await sio.emit("send_message_global", socket_response)

    new_global_message = GlobalMessage(
        body=message_body, sender_name=users_username, sender_id=users_id, timestamp=now
    )
    db.add(new_global_message)
    await db.commit()
    return {"result": True, "message": "success"}
