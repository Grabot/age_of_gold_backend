from datetime import datetime
from typing import Optional

from fastapi import Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.api_v1 import api_router_v1
from app.api.rest_util import get_failed_response
from app.database import get_db
from app.models import Guild, User
from app.models.message import GuildMessage
from app.sockets.sockets import sio
from app.util.util import check_token, get_auth_token


class SendMessageGuildRequest(BaseModel):
    guild_id: int
    message: str


@api_router_v1.post("/send/message/guild", status_code=200)
async def send_guild_message(
    send_message_guild_request: SendMessageGuildRequest,
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

    message_body = send_message_guild_request.message
    guild_id = send_message_guild_request.guild_id

    guild_send_statement = (
        select(Guild).where(Guild.guild_id == guild_id).where(Guild.accepted == True)
    )
    guild_send_results = await db.execute(guild_send_statement)
    guild_send_result = guild_send_results.first()
    if not guild_send_result:
        return get_failed_response("guild not found", response)

    now = datetime.utcnow()

    guild_room = f"guild_{guild_id}"
    print(f"sending a guild message to room {guild_room}")
    socket_response = {
        "sender_name": user_send.username,
        "sender_id": user_send.id,
        "message": message_body,
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%S.%f"),
    }

    await sio.emit(
        "send_message_guild",
        socket_response,
        room=guild_room,
    )

    new_guild_message = GuildMessage(
        body=message_body,
        guild_id=guild_id,
        sender_name=user_send.username,
        sender_id=user_send.id,
        timestamp=now,
    )

    db.add(new_guild_message)
    await db.commit()

    return {
        "result": True,
    }
