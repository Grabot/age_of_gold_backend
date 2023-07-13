from typing import Optional

from fastapi import Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.api_v1 import api_router_v1
from app.api.rest_util import get_failed_response
from app.database import get_db
from app.models import User
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
        await db.delete(guild_to_leave)
        await db.commit()
        # TODO: check if there are other member and if someone needs to be given the leader role.

    return {
        "result": True,
        "message": "left",
    }
