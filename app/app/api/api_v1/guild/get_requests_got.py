from typing import Optional

from fastapi import Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.api.api_v1 import api_router_v1
from app.api.rest_util import get_failed_response
from app.database import get_db
from app.models import User
from app.models.guild import Guild
from app.util.util import check_token, get_auth_token


# The requests of a user to guilds that come from the guild
@api_router_v1.post("/guild/requests/user/got", status_code=200)
async def get_requests_user_got(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    print("start guild get send requests")

    auth_token = get_auth_token(request.headers.get("Authorization"))

    if auth_token == "":
        get_failed_response("An error occurred", response)

    user: Optional[User] = await check_token(db, auth_token)
    if not user:
        get_failed_response("An error occurred", response)

    guild_statement = (
        select(Guild)
        .where(Guild.user_id == user.id)
        .where(Guild.requested == False)
        .where(Guild.accepted == False)
    )
    results = await db.execute(guild_statement)
    result = results.all()

    if not result:
        return get_failed_response("no requests found", response)

    guild_requests = []
    for guilds in result:
        guild = guilds.Guild
        guild_requests.append(guild.serialize)

    return {
        "result": True,
        "guild_requests": guild_requests,
    }


class ReceivedRequest(BaseModel):
    guild_id: int


# The responses gotten by a guild from users made by users
@api_router_v1.post("/guild/requests/guild/got", status_code=200)
async def get_requests_guild_got(
    received_request: ReceivedRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    print("start guild get got requests")

    auth_token = get_auth_token(request.headers.get("Authorization"))

    if auth_token == "":
        get_failed_response("An error occurred", response)

    user: Optional[User] = await check_token(db, auth_token)
    if not user:
        get_failed_response("An error occurred", response)

    guild_id = received_request.guild_id
    guild_statement = (
        select(Guild)
        .where(Guild.guild_id == guild_id)
        .where(Guild.requested == False)
        .where(Guild.accepted == False)
    ).options(selectinload(Guild.guild_member))
    results = await db.execute(guild_statement)
    result = results.all()

    if not result:
        return get_failed_response("no requests found", response)

    guild_requests = []
    for guilds in result:
        guild = guilds.Guild
        user_requested = guild.guild_member
        guild_requests.append(user_requested.serialize_minimal)

    return {
        "result": True,
        "guild_requests": guild_requests,
    }
