from typing import Optional

from fastapi import Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.api_v1 import api_router_v1
from app.api.rest_util import get_failed_response
from app.database import get_db
from app.models import Guild, User
from app.util.util import check_token, get_auth_token


class NewMemberRequest(BaseModel):
    user_id: int


@api_router_v1.post("/guild/member/new", status_code=200)
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

    user: Optional[User] = await check_token(db, auth_token, True)
    if not user:
        get_failed_response("An error occurred", response)

    # The guild to join is the guild of the user who requested to join
    guild_to_join = user.guild
    if guild_to_join is None:
        get_failed_response("No guild found", response)

    user_id = new_member_request.user_id
    user_statement = select(User).where(User.id == user_id)
    results = await db.execute(user_statement)
    result = results.first()

    if not result:
        return get_failed_response("no user found", response)

    found_user: User = result.User

    statement_guild_user = (
        select(Guild)
        .where(Guild.user_id == found_user.id)
        .where(Guild.guild_id == guild_to_join.guild_id)
    )
    results_guild_user = await db.execute(statement_guild_user)
    result_guild_user = results_guild_user.first()

    if result_guild_user is not None:
        print("guild query user")
        # TODO?
    else:
        guild = Guild(
            user_id=found_user.id,
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
