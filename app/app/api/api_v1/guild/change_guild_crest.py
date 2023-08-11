from datetime import datetime
from typing import Optional

from fastapi import Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, update

from app.api.api_v1 import api_router_v1
from app.api.api_v1.guild.create_guild import save_guild_crest
from app.api.rest_util import get_failed_response
from app.database import get_db
from app.models import Guild, User
from app.sockets.sockets import sio
from app.util.util import check_token, get_auth_token


class ChangeGuildCrestRequest(BaseModel):
    guild_id: int
    guild_crest: Optional[str] = None


@api_router_v1.post("/guild/change/crest", status_code=200)
async def change_guild_crest(
    change_guild_crest_request: ChangeGuildCrestRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    print("start change guild crest request")
    auth_token = get_auth_token(request.headers.get("Authorization"))

    if auth_token == "":
        return get_failed_response("An error occurred", response)

    user: Optional[User] = await check_token(db, auth_token)
    if not user:
        return get_failed_response("An error occurred", response)

    guild_id = change_guild_crest_request.guild_id

    guild_statement = (
        select(Guild)
        .where(Guild.guild_id == guild_id)
        .where(Guild.user_id == user.id)
        .where(Guild.accepted == True)
    )
    results = await db.execute(guild_statement)
    result = results.first()

    if not result:
        return get_failed_response("no guild request found", response)

    check_guild: Guild = result.Guild
    guild_crest = change_guild_crest_request.guild_crest

    if guild_crest is None and not check_guild.default_crest:
        print("new crest is default, but previous was not!!!!")
        # We are updating the crest to be the default, so update the member objects
        update_guild_members = (
            update(Guild).values(default_crest=True).where(Guild.guild_id == guild_id)
        )
        await db.execute(update_guild_members)
        await db.commit()
    elif guild_crest is not None and check_guild.default_crest:
        print("new crest is an image, but previous was default!!!!")
        update_guild_members = (
            update(Guild).values(default_crest=False).where(Guild.guild_id == guild_id)
        )
        await db.execute(update_guild_members)
        await db.commit()

    if guild_crest is not None:
        save_guild_crest(check_guild, guild_crest)

    now = datetime.utcnow()
    socket_response = {
        "guild_avatar": guild_crest,
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%S.%f"),
    }

    guild_room = f"guild_{guild_id}"
    await sio.emit(
        "guild_crest_changed",
        socket_response,
        room=guild_room,
    )

    return {
        "result": True,
        "message": "guild crest changed",
    }
