from typing import Optional

from fastapi import Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import update

from app.api.api_v1 import api_router_v1
from app.api.rest_util import get_failed_response
from app.database import get_db
from app.models import Guild, User
from app.util.util import check_token, get_auth_token


@api_router_v1.get("/guild/leave", status_code=200)
async def leave_guild(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    print("start guild leave")
    auth_token = get_auth_token(request.headers.get("Authorization"))

    if auth_token == "":
        get_failed_response("An error occurred", response)

    user: Optional[User] = await check_token(db, auth_token, True)
    if not user:
        get_failed_response("An error occurred", response)

    guild_to_leave = user.guild
    if guild_to_leave is not None:
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

    return {
        "result": True,
        "message": "left",
    }
