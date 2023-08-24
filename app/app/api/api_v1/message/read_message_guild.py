from fastapi import Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.api_v1 import api_router_v1
from app.api.rest_util import get_failed_response
from app.database import get_db
from app.models import Guild
from app.util.util import check_token, get_auth_token


class ReadMessageGuildRequest(BaseModel):
    guild_id: int


@api_router_v1.post("/read/message/guild", status_code=200)
async def read_personal_message(
    request: Request,
    read_message_guild_request: ReadMessageGuildRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    auth_token = get_auth_token(request.headers.get("Authorization"))
    if auth_token == "":
        return get_failed_response("an error occurred", response)

    user_request = await check_token(db, auth_token)
    if not user_request:
        return get_failed_response("an error occurred", response)

    guild_id = read_message_guild_request.guild_id

    statement_guild_read = (
        select(Guild)
        .where(Guild.guild_id == guild_id)
        .where(Guild.user_id == user_request.id)
        .where(Guild.accepted == True)
    )
    guild_read_results = await db.execute(statement_guild_read)
    guild_read_result = guild_read_results.first()
    if not guild_read_result:
        return get_failed_response("user not found", response)

    guild_user: Guild = guild_read_result.Guild
    guild_user.read_messages()
    db.add(guild_user)
    await db.commit()

    return {"result": True, "message": "success"}
