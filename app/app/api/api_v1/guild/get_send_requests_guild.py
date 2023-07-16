from typing import Optional

from fastapi import Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.api_v1 import api_router_v1
from app.api.rest_util import get_failed_response
from app.database import get_db
from app.models import User
from app.models.guild import Guild
from app.util.util import check_token, get_auth_token


@api_router_v1.get("/guild/requests/get/send", status_code=200)
async def get_send_requests_guild(
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
        .where(Guild.requested == True)
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
