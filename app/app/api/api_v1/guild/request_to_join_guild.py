from typing import Optional

from fastapi import Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.api_v1 import api_router_v1
from app.api.rest_util import get_failed_response
from app.database import get_db
from app.models import User
from app.models.guild import Guild
from app.util.util import check_token, get_auth_token


class RequestToJoinRequest(BaseModel):
    guild_id: int


@api_router_v1.post("/guild/request", status_code=200)
async def request_to_join_guild(
    request_to_join_request: RequestToJoinRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    print("start guild request")
    auth_token = get_auth_token(request.headers.get("Authorization"))

    if auth_token == "":
        get_failed_response("An error occurred", response)

    user: Optional[User] = await check_token(db, auth_token, True)
    if not user:
        get_failed_response("An error occurred", response)

    print("user found")
    guild_user = user.guild
    # The user has to not be part of a guild
    if guild_user is not None:
        print("guild found")
        return get_failed_response("already part of a guild", response)

    guild_id = request_to_join_request.guild_id
    statement_guild = select(Guild).where(Guild.guild_id == guild_id)
    results_guild = await db.execute(statement_guild)
    result_guild = results_guild.first()

    print("guild query")
    if result_guild is None:
        print("guild query error")
        return get_failed_response("an error occurred", response)

    print("guild query fine")
    guild_to_join: Guild = result_guild.Guild

    statement_guild_user = (
        select(Guild).where(Guild.guild_id == guild_id).where(Guild.user_id == user.id)
    )
    results_guild_user = await db.execute(statement_guild_user)
    result_guild_user = results_guild_user.first()

    print("guild query user")
    if result_guild_user is not None:
        guild_request: Guild = result_guild_user.Guild
        if guild_request.requested is True:
            return get_failed_response("Guild already requested", response)
        else:
            # TODO: Just accept the guild request in this case.
            return get_failed_response("Guild requested YOU!", response)
    else:
        guild = Guild(
            user_id=user.id,
            guild_id=guild_to_join.guild_id,
            guild_name=guild_to_join.guild_name,
            member_ids=guild_to_join.member_ids,
            default_crest=guild_to_join.default_crest,
            accepted=False,
            requested=True,
        )
        db.add(guild)
        await db.commit()
        # The guild id is not set on the user yet, because it has to be accepted first.

        return {
            "result": True,
            "message": "requested to join",
        }
