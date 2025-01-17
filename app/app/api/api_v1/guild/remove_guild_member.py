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


class RemoveGuildMemberRequest(BaseModel):
    remove_member_id: int
    guild_id: int


@api_router_v1.post("/guild/remove/member", status_code=200)
async def remove_guild_member(
    remove_guild_member_request: RemoveGuildMemberRequest,
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

    users_guild: Guild = user.guild
    if not users_guild:
        return get_failed_response("An error occurred", response)

    # check if the user has the permission to remove someone.
    # Find the list of users that have this user id,
    # which will be a list of 1 so take the first element.
    member_ids = users_guild.member_ids
    current_member = [member_id for member_id in member_ids if member_id[0] == user.id][0]

    if current_member[1] >= 2:
        # The permission needs to be 0 or 1 to remove someone.
        return get_failed_response("No permission to remove someone", response)

    remove_member_id = remove_guild_member_request.remove_member_id
    guild_id = remove_guild_member_request.guild_id
    if guild_id != users_guild.guild_id:
        return get_failed_response("An error occurred", response)

    remove_member = [member_id for member_id in member_ids if member_id[0] == remove_member_id][0]
    if current_member[1] >= remove_member[1]:
        return get_failed_response(
            "No permission to kick a member of someone that has the same or higher rank than you",
            response,
        )

    guild_statement = (
        select(Guild)
        .where(Guild.guild_id == guild_id)
        .where(Guild.user_id == remove_member_id)
        .where(Guild.accepted == True)
    )
    results = await db.execute(guild_statement)
    result = results.first()

    if not result:
        return get_failed_response("no guild user found", response)

    guild_to_leave: Guild = result.Guild
    new_member_ids = [member_id for member_id in member_ids if member_id[0] != remove_member_id]
    update_guild_members = (
        update(Guild)
        .values(member_ids=new_member_ids)
        .where(Guild.guild_id == guild_to_leave.guild_id)
        .where(Guild.accepted == True)
    )
    await db.execute(update_guild_members)
    await db.delete(guild_to_leave)
    await db.commit()

    now = datetime.now(pytz.utc).replace(tzinfo=None)
    socket_response = {
        "member_removed": {
            "user_id": remove_member_id,
        },
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%S.%f"),
    }

    guild_room = f"guild_{guild_id}"
    await sio.emit(
        "guild_member_removed",
        socket_response,
        room=guild_room,
    )

    return {
        "result": True,
        "message": "member removed",
    }
