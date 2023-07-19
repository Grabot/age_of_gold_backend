from typing import Optional

from fastapi import Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, update

from app.api.api_v1 import api_router_v1
from app.api.rest_util import get_failed_response
from app.database import get_db
from app.models import Guild, User
from app.util.util import check_token, get_auth_token


class GuildAcceptRequest(BaseModel):
    guild_id: int


@api_router_v1.post("/guild/request/accept", status_code=200)
async def accept_guild_request(
    guild_accept_request: GuildAcceptRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    auth_token = get_auth_token(request.headers.get("Authorization"))

    if auth_token == "":
        get_failed_response("An error occurred", response)

    user: Optional[User] = await check_token(db, auth_token, True)
    if not user:
        get_failed_response("An error occurred", response)

    users_guild = user.guild
    if users_guild is not None:
        # The user cannot accept a request if it's part of a guild, something went wrong.
        get_failed_response("An error occurred", response)

    print("accepting guild request!")
    # First remove all Guild objects of the users, meaning all requests made by the user
    # or sent to the user will be removed. This is because the user has accepted a request
    guild_statement = select(Guild).where(Guild.user_id == user.id)
    results_guild_user = await db.execute(guild_statement)
    result_guild_user = results_guild_user.all()

    for guild_request in result_guild_user:
        print(f"going to remove: {guild_request.Guild}")
        await db.delete(guild_request.Guild)

    print("removed!")
    guild_id = guild_accept_request.guild_id
    statement_guild = select(Guild).where(Guild.guild_id == guild_id).where(Guild.accepted == True)
    results_guild = await db.execute(statement_guild)
    users_guild = results_guild.all()

    if users_guild is None:
        return get_failed_response("an error occurred", response)

    print("guild query fine. Got all guild members")
    guild_to_join: Guild = users_guild[0].Guild

    member_ids = guild_to_join.member_ids
    member_rank = [user.id, 4]
    member_ids.append(member_rank)
    print(f"member ids: {member_ids}")

    update_guild_members = (
        update(Guild)
        .values(member_ids=member_ids)
        .where(Guild.guild_id == guild_id)
        .where(Guild.accepted == True)
    )
    results = await db.execute(update_guild_members)
    print("update guild members: %s" % results)

    guild = Guild(
        user_id=user.id,
        guild_id=guild_to_join.guild_id,
        guild_name=guild_to_join.guild_name,
        member_ids=member_ids,
        default_crest=guild_to_join.default_crest,
        requested=None,  # no longer important.
        accepted=True,
    )
    db.add(guild)
    await db.commit()

    return {"result": True, "message": "guild join"}
