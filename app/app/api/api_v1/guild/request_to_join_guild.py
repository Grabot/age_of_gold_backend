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


@api_router_v1.post("/guild/request/user", status_code=200)
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
    statement_guild = select(Guild).where(Guild.guild_id == guild_id).where(Guild.accepted == True)
    results_guild = await db.execute(statement_guild)
    result_guild = results_guild.all()

    if result_guild is None:
        return get_failed_response("an error occurred", response)

    guild_to_join: Guild = result_guild[0].Guild

    statement_guild_user_request = (
        select(Guild)
        .where(Guild.guild_id == guild_id)
        .where(Guild.user_id == user.id)
        .where(Guild.requested == True)
    )
    results_guild_user_request = await db.execute(statement_guild_user_request)
    result_guild_user_request = results_guild_user_request.first()

    if result_guild_user_request is not None:
        return get_failed_response("Guild already requested", response)

    statement_guild_user_not_request = (
        select(Guild)
        .where(Guild.guild_id == guild_id)
        .where(Guild.user_id == user.id)
        .where(Guild.requested == False)
    )
    results_guild_user_not_request = await db.execute(statement_guild_user_not_request)
    result_guild_user_not_request = results_guild_user_not_request.first()
    if result_guild_user_not_request is not None:
        # The guild requested this user already, it should not be possible to request.
        # On the frontend it should have caught the request and send an acceptation instead.
        return get_failed_response("An error occurred", response)

    guild = Guild(
        user_id=user.id,
        guild_id=guild_to_join.guild_id,
        guild_name=guild_to_join.guild_name,
        member_ids=guild_to_join.member_ids,
        default_crest=guild_to_join.default_crest,
        requested=True,
        accepted=False,
    )
    db.add(guild)
    await db.commit()

    return {
        "result": True,
        "message": "requested to join",
    }


class NewMemberRequest(BaseModel):
    user_id: int
    guild_id: int


@api_router_v1.post("/guild/request/guild", status_code=200)
async def new_member(
    new_member_request: NewMemberRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    print("start new member request")
    auth_token = get_auth_token(request.headers.get("Authorization"))

    if auth_token == "":
        get_failed_response("An error occurred", response)

    user: Optional[User] = await check_token(db, auth_token)
    if not user:
        get_failed_response("An error occurred", response)

    user_id = new_member_request.user_id
    guild_id = new_member_request.guild_id

    # First check if the user is already in a guild.
    statement_user_guild = (
        select(Guild).where(Guild.user_id == user_id).where(Guild.accepted == True)
    )
    results_user_guild = await db.execute(statement_user_guild)
    result_user_guild = results_user_guild.first()
    if result_user_guild is not None:
        return get_failed_response("User already in a guild", response)

    # Get the guild objects
    statement_guild = select(Guild).where(Guild.guild_id == guild_id).where(Guild.accepted == True)
    results_guild = await db.execute(statement_guild)
    result_guild = results_guild.all()

    if result_guild is None:
        return get_failed_response("an error occurred", response)

    statement_user_guild_not_request = (
        select(Guild)
        .where(Guild.user_id == user_id)
        .where(Guild.guild_id == guild_id)
        .where(Guild.requested == False)
    )
    results_user_guild_not_request = await db.execute(statement_user_guild_not_request)
    result_user_guild_not_request = results_user_guild_not_request.first()

    if result_user_guild_not_request is not None:
        return get_failed_response("User is already requested", response)

    statement_user_guild_request = (
        select(Guild)
        .where(Guild.user_id == user_id)
        .where(Guild.guild_id == guild_id)
        .where(Guild.requested == True)
    )
    results_user_guild_request = await db.execute(statement_user_guild_request)
    result_user_guild_request = results_user_guild_request.first()
    if result_user_guild_request is not None:
        # The user requested this guild already, it should not be possible to request.
        # On the frontend it should have caught the request and send an acceptation instead.
        return get_failed_response("An error occurred", response)

    guild_to_join: Guild = result_guild[0].Guild

    guild = Guild(
        user_id=user_id,
        guild_id=guild_to_join.guild_id,
        guild_name=guild_to_join.guild_name,
        member_ids=guild_to_join.member_ids,
        default_crest=guild_to_join.default_crest,
        requested=False,
        accepted=False,
    )
    db.add(guild)
    await db.commit()

    return {
        "result": True,
        "message": "request send",
    }
