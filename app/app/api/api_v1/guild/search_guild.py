from typing import Optional

from fastapi import Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.api_v1 import api_router_v1
from app.api.rest_util import get_failed_response
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
        get_failed_response("An error occurred", response)

    user: Optional[User] = await check_token(db, auth_token)
    if not user:
        get_failed_response("An error occurred", response)

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
