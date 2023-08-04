from datetime import datetime
from typing import Optional

from fastapi import Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.api_v1 import api_router_v1
from app.api.rest_util import get_failed_response
from app.database import get_db
from app.models import Guild, User
from app.sockets.sockets import sio
from app.util.util import check_token, get_auth_token


class CancelGuildRequestUserRequest(BaseModel):
    guild_id: int
    user_id: int


@api_router_v1.post("/guild/request/cancel/user", status_code=200)
async def cancel_guild_request_user(
    cancel_guild_request_user_request: CancelGuildRequestUserRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    print("start guild cancel request")
    auth_token = get_auth_token(request.headers.get("Authorization"))

    if auth_token == "":
        return get_failed_response("An error occurred", response)

    user: Optional[User] = await check_token(db, auth_token)
    if not user:
        return get_failed_response("An error occurred", response)

    guild_id = cancel_guild_request_user_request.guild_id
    user_id = cancel_guild_request_user_request.user_id
    guild_statement = (
        select(Guild)
        .where(Guild.guild_id == guild_id)
        .where(Guild.user_id == user_id)
        .where(Guild.requested == True)
    )
    results = await db.execute(guild_statement)
    result = results.first()

    if not result:
        return get_failed_response("no guild request found", response)

    found_guild: Guild = result.Guild
    if found_guild is None:
        return get_failed_response("something went wrong", response)

    await db.delete(found_guild)
    await db.commit()

    now = datetime.utcnow()
    socket_response_guild = {
        "member_cancelled": {
            "user_id": user_id,
        },
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%S.%f"),
    }

    guild_room = f"guild_{guild_id}"
    await sio.emit(
        "guild_request_cancelled",
        socket_response_guild,
        room=guild_room,
    )

    socket_response_user = {
        "guild_id": guild_id,
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%S.%f"),
    }
    member_asked_room = f"room_{user_id}"
    await sio.emit(
        "guild_request_denied",
        socket_response_user,
        room=member_asked_room,
    )

    return {
        "result": True,
        "message": "cancelled request",
    }


class CancelGuildRequestGuildRequest(BaseModel):
    guild_id: int
    user_id: int


@api_router_v1.post("/guild/request/cancel/guild", status_code=200)
async def cancel_guild_request_guild(
    cancel_guild_request_guild_request: CancelGuildRequestGuildRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    print("start guild cancel request")
    auth_token = get_auth_token(request.headers.get("Authorization"))

    if auth_token == "":
        return get_failed_response("An error occurred", response)

    user: Optional[User] = await check_token(db, auth_token, True)
    if not user:
        return get_failed_response("An error occurred", response)

    user_id = cancel_guild_request_guild_request.user_id
    guild_id = cancel_guild_request_guild_request.guild_id
    guild_statement = (
        select(Guild)
        .where(Guild.guild_id == guild_id)
        .where(Guild.user_id == user_id)
        .where(Guild.requested == False)
    )
    results = await db.execute(guild_statement)
    result = results.first()

    if not result:
        return get_failed_response("no guild request found", response)

    found_guild: Guild = result.Guild
    if found_guild is None:
        return get_failed_response("something went wrong", response)

    await db.delete(found_guild)
    await db.commit()

    now = datetime.utcnow()
    socket_response_guild = {
        "member_cancelled": {
            "user_id": user_id,
        },
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%S.%f"),
    }

    guild_room = f"guild_{guild_id}"
    await sio.emit(
        "guild_request_cancelled",
        socket_response_guild,
        room=guild_room,
    )

    socket_response_user = {
        "guild_id": guild_id,
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%S.%f"),
    }
    member_cancelled_room = f"room_{user_id}"
    await sio.emit(
        "guild_request_denied",
        socket_response_user,
        room=member_cancelled_room,
    )

    return {
        "result": True,
        "message": "cancelled request",
    }
