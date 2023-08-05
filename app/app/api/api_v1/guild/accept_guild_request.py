from datetime import datetime
from typing import Optional

from fastapi import Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, update

from app.api.api_v1 import api_router_v1
from app.api.rest_util import get_failed_response
from app.database import get_db
from app.models import Guild, User
from app.sockets.sockets import sio
from app.util.util import check_token, get_auth_token


async def join_guild(db: AsyncSession, user_id: int, guild_to_join: Guild):
    print("accepting guild request!")
    # First remove all Guild objects of the users, meaning all requests made by the user
    # or sent to the user will be removed. This is because the user has accepted a request
    guild_statement = select(Guild).where(Guild.user_id == user_id).where(Guild.accepted == False)
    results_guild_user = await db.execute(guild_statement)
    result_guild_user = results_guild_user.all()

    for guild_request in result_guild_user:
        print(f"going to remove: {guild_request.Guild}")
        await db.delete(guild_request.Guild)

    print("removed!")
    member_ids = guild_to_join.member_ids
    member_rank = [user_id, 3]
    member_ids.append(member_rank)
    print(f"member ids: {member_ids}")

    update_guild_members = (
        update(Guild)
        .values(member_ids=member_ids)
        .where(Guild.guild_id == guild_to_join.guild_id)
        .where(Guild.accepted == True)
    )
    await db.execute(update_guild_members)

    guild = Guild(
        user_id=user_id,
        guild_id=guild_to_join.guild_id,
        guild_name=guild_to_join.guild_name,
        member_ids=member_ids,
        default_crest=guild_to_join.default_crest,
        requested=None,  # no longer important.
        accepted=True,
    )
    db.add(guild)
    await db.commit()

    now = datetime.utcnow()
    socket_response = {
        "member": {
            "user_id": user_id,
            "rank": 3,
        },
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%S.%f"),
    }

    guild_room = f"guild_{guild_to_join.guild_id}"
    await sio.emit(
        "guild_new_member",
        socket_response,
        room=guild_room,
    )

    return guild


class GuildAcceptRequestGuild(BaseModel):
    guild_id: int


@api_router_v1.post("/guild/request/accept/guild", status_code=200)
async def accept_guild_request_guild(
    guild_accept_request_guild: GuildAcceptRequestGuild,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    auth_token = get_auth_token(request.headers.get("Authorization"))

    if auth_token == "":
        return get_failed_response("An error occurred", response)

    user: Optional[User] = await check_token(db, auth_token, True)
    if not user:
        return get_failed_response("An error occurred", response)

    users_guild = user.guild
    if users_guild is not None:
        # The user cannot accept a request if it's part of a guild, something went wrong.
        return get_failed_response("An error occurred", response)

    guild_id = guild_accept_request_guild.guild_id
    statement_guild = select(Guild).where(Guild.guild_id == guild_id).where(Guild.accepted == True)
    results_guild = await db.execute(statement_guild)
    users_guild = results_guild.all()

    if users_guild is None or users_guild == []:
        return get_failed_response("an error occurred", response)

    print("guild query fine. Got all guild members")
    guild_to_join: Guild = users_guild[0].Guild
    new_guild = await join_guild(db, user.id, guild_to_join)

    return {"result": True, "guild": new_guild.serialize}


class GuildAcceptRequestUser(BaseModel):
    user_id: int
    guild_id: int


@api_router_v1.post("/guild/request/accept/user", status_code=200)
async def accept_guild_request_user(
    guild_accept_request_user: GuildAcceptRequestUser,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    auth_token = get_auth_token(request.headers.get("Authorization"))

    if auth_token == "":
        return get_failed_response("An error occurred", response)

    user: Optional[User] = await check_token(db, auth_token, True)
    if not user:
        return get_failed_response("An error occurred", response)

    print("Initial check user")
    # Check if the user is part of a guild. This should not be the case.
    user_id = guild_accept_request_user.user_id
    user_statement = select(Guild).where(Guild.user_id == user_id).where(Guild.accepted == True)
    results_user = await db.execute(user_statement)
    result_user = results_user.first()

    if result_user is not None:
        return get_failed_response("An error occurred", response)

    guild_id = guild_accept_request_user.guild_id
    statement_guild = select(Guild).where(Guild.guild_id == guild_id).where(Guild.accepted == True)
    results_guild = await db.execute(statement_guild)
    users_guild = results_guild.all()

    if users_guild is None or users_guild == []:
        return get_failed_response("an error occurred", response)

    print("guild query fine. Got all guild members")
    guild_to_join: Guild = users_guild[0].Guild
    await join_guild(db, user_id, guild_to_join)

    now = datetime.utcnow()
    socket_response_user = {
        "guild": guild_to_join.serialize_minimal,
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%S.%f"),
    }
    member_accepted_room = f"room_{user_id}"
    await sio.emit(
        "guild_accepted_member",
        socket_response_user,
        room=member_accepted_room,
    )

    return {"result": True, "message": "guild join"}
