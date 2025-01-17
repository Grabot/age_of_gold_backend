from datetime import datetime
from typing import Optional

from fastapi import Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import delete, select, update

from app.api.api_v1 import api_router_v1
from app.util.rest_util import get_failed_response
from app.database import get_db
from app.models import Guild, User
from app.sockets.sockets import sio
from app.util.util import check_token, get_auth_token
import pytz


class LeaveGuildRequest(BaseModel):
    user_id: int
    guild_id: int


@api_router_v1.post("/guild/leave", status_code=200)
async def leave_guild(
    leave_guild_request: LeaveGuildRequest,
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

    guild_id = leave_guild_request.guild_id
    user_id = leave_guild_request.user_id

    guild_statement = (
        select(Guild)
        .where(Guild.guild_id == guild_id)
        .where(Guild.user_id == user_id)
        .where(Guild.accepted == True)
    )
    results = await db.execute(guild_statement)
    result = results.first()

    if not result:
        return get_failed_response("no guild request found", response)

    guild_to_leave: Guild = result.Guild
    member_ids = guild_to_leave.member_ids
    # Find the list of users that have this user id,
    # which will be a list of 1 so take the first element.
    current_member = [member_id for member_id in member_ids if member_id[0] == user.id][0]
    # Get the remaining members without the user id of the one leaving.
    new_member_ids = [member_id for member_id in member_ids if member_id[0] != user.id]
    # Check if the current_member that is going to leave is the guild leader.
    if current_member[1] == 0:
        # If it is, pick a random member and give him the leader role
        if len(new_member_ids) > 0:
            new_member_ids[0][1] = 0

    update_guild_members = (
        update(Guild)
        .values(member_ids=new_member_ids)
        .where(Guild.guild_id == guild_to_leave.guild_id)
        .where(Guild.accepted == True)
    )
    await db.execute(update_guild_members)
    await db.delete(guild_to_leave)
    await db.commit()

    # final check if you were the last member of the guild. In that case remove all requests
    guild_statement = (
        select(Guild).where(Guild.guild_id == guild_to_leave.guild_id).where(Guild.accepted == True)
    )
    results = await db.execute(guild_statement)
    result = results.first()
    if not result:
        delete_guild_objects = delete(Guild).where(Guild.guild_id == guild_to_leave.guild_id)
        await db.execute(delete_guild_objects)
        await db.commit()

    now = datetime.now(pytz.utc).replace(tzinfo=None)
    socket_response = {
        "member_removed": {
            "user_id": user_id,
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
        "message": "left",
    }
