from fastapi import Depends, Request
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic import BaseModel
from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.api_v1 import api_router_v1
from app.database import get_db
from app.models.message import GuildMessage
from app.util.util import check_token, get_auth_token


def get_failed_response_messages():
    return {"items": [], "total": 0, "page": 1, "size": 1, "pages": 0}


class GetMessageGuildRequest(BaseModel):
    guild_id: int


@api_router_v1.post("/get/message/guild", response_model=Page[GuildMessage], status_code=200)
async def get_guild_message(
    get_message_guild_request: GetMessageGuildRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    print(f"header {request}")
    auth_token = get_auth_token(request.headers.get("Authorization"))
    print(f"token {auth_token}")
    if auth_token == "":
        return get_failed_response_messages()

    user = await check_token(db, auth_token)
    if not user:
        return get_failed_response_messages()

    guild_id = get_message_guild_request.guild_id

    return await paginate(
        db, select(GuildMessage).filter_by(guild_id=guild_id).order_by(desc(GuildMessage.timestamp))
    )
