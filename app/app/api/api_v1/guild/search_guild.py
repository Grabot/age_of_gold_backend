from typing import Optional

from fastapi import Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.api_v1 import api_router_v1
from app.util.rest_util import get_failed_response
from app.database import get_db
from app.models import Guild, User
from app.util.util import check_token, get_auth_token


class SearchGuildRequest(BaseModel):
    guild_name: str


@api_router_v1.post("/guild/search", status_code=200)
async def search_guild(
    search_guild_request: SearchGuildRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    auth_token = get_auth_token(request.headers.get("Authorization"))

    if auth_token == "":
        return get_failed_response("An error occurred", response)

    user: Optional[User] = await check_token(db, auth_token)
    if not user:
        return get_failed_response("An error occurred", response)

    guild_name = search_guild_request.guild_name
    guild_statement = (
        select(Guild)
        .where(func.lower(Guild.guild_name) == guild_name.lower())
        .where(Guild.accepted == True)
    )
    results = await db.execute(guild_statement)
    result = results.first()

    if not result:
        return get_failed_response("no guilds found", response)

    found_guild: Guild = result.Guild

    return {"result": True, "guild": found_guild.serialize}


class GetGuildRequest(BaseModel):
    guild_id: int
    user_id: int


@api_router_v1.post("/guild/get", status_code=200)
async def get_guild(
    get_guild_request: GetGuildRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    auth_token = get_auth_token(request.headers.get("Authorization"))

    if auth_token == "":
        return get_failed_response("An error occurred", response)

    user: Optional[User] = await check_token(db, auth_token)
    if not user:
        return get_failed_response("An error occurred", response)

    guild_id = get_guild_request.guild_id
    user_id = get_guild_request.user_id
    guild_statement = (
        select(Guild)
        .where(Guild.guild_id == guild_id)
        .where(Guild.user_id == user_id)
        .where(Guild.accepted == True)
    )
    results = await db.execute(guild_statement)
    result = results.first()

    if not result:
        return get_failed_response("no guilds found", response)

    found_guild: Guild = result.Guild

    return {"result": True, "guild": found_guild.serialize}
