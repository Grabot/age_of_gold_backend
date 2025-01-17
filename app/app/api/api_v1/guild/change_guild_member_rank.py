from datetime import datetime
from typing import Optional

from fastapi import Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, update

from app.api.api_v1 import api_router_v1
from app.util.rest_util import get_failed_response
from app.database import get_db
from app.models import Guild, User
from app.sockets.sockets import sio
from app.util.util import check_token, get_auth_token
import pytz


class ChangeGuildMemberRankRequest(BaseModel):
    changed_member_id: int
    guild_id: int
    new_rank: int


@api_router_v1.post("/guild/change/member/rank", status_code=200)
async def change_guild_member_rank(
    change_guild_member_rank_request: ChangeGuildMemberRankRequest,
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

    logged_in_guild: Optional[Guild] = user.guild
    if not logged_in_guild:
        return get_failed_response("An error occurred", response)

    member_ids = logged_in_guild.member_ids
    current_member = [member_id for member_id in member_ids if member_id[0] == user.id][0]
    if current_member[1] >= 2:
        # The permission needs to be 0 or 1 to remove someone.
        return get_failed_response("No permission to change someone's rank", response)

    guild_id = change_guild_member_rank_request.guild_id
    changed_member_id = change_guild_member_rank_request.changed_member_id
    new_rank = change_guild_member_rank_request.new_rank
    change_member = [member_id for member_id in member_ids if member_id[0] == changed_member_id][0]

    if current_member[1] >= change_member[1]:
        return get_failed_response(
            "No permission to change the rank of someone with a higher or similar rank to you",
            response,
        )
    if current_member[1] >= new_rank:
        return get_failed_response(
            "No permission to change the rank of someone to be higher than your rank", response
        )

    if guild_id != logged_in_guild.guild_id:
        return get_failed_response("An error occurred", response)

    guild_statement = (
        select(Guild)
        .where(Guild.guild_id == guild_id)
        .where(Guild.user_id == changed_member_id)
        .where(Guild.accepted == True)
    )
    results = await db.execute(guild_statement)
    result = results.first()
    if not result:
        return get_failed_response("no guild user found", response)

    guild_to_change_rank: Guild = result.Guild
    member_ids = guild_to_change_rank.member_ids
    for m in range(0, len(member_ids)):
        member = member_ids[m]
        if member[0] == changed_member_id:
            if member[1] == new_rank:
                return get_failed_response("Rank is the same", response)
            else:
                member[1] = new_rank
                break

    update_guild_members = (
        update(Guild)
        .values(member_ids=member_ids)
        .where(Guild.guild_id == guild_to_change_rank.guild_id)
        .where(Guild.accepted == True)
    )
    await db.execute(update_guild_members)
    await db.commit()

    now = datetime.now(pytz.utc).replace(tzinfo=None)
    socket_response = {
        "member_changed": {
            "user_id": changed_member_id,
            "new_rank": new_rank,
        },
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%S.%f"),
    }

    guild_room = f"guild_{guild_id}"
    await sio.emit(
        "member_changed_rank",
        socket_response,
        room=guild_room,
    )

    return {
        "result": True,
        "message": "guild member rank changed",
    }
