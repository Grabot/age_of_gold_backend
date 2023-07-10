from typing import Optional

from fastapi import Depends, Response
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.api_v1 import api_router_v1
from app.api.rest_util import get_failed_response
from app.database import get_db
from app.models.guild import Guild


class CreateGuildRequest(BaseModel):
    user_id: int
    guild_name: Optional[str] = None
    guild_crest: Optional[str] = None


@api_router_v1.post("/guild/create", status_code=200)
async def create_guild(
    create_guild_request: CreateGuildRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    print("start guild create")
    user_id = create_guild_request.user_id
    guild_name = create_guild_request.guild_name
    guild_crest = create_guild_request.guild_crest

    statement_guild_name = select(Guild).where(func.lower(Guild.guild_name) == guild_name.lower())
    results_guild_name = await db.execute(statement_guild_name)
    result_guild_name = results_guild_name.first()

    print(f"results: {result_guild_name}")
    if result_guild_name is not None:
        return get_failed_response(
            "Guild name is already taken, please choose a different one.", response
        )

    guild = Guild(user_id=user_id, guild_name=guild_name, guild_crest=guild_crest, member_ids=[])
    db.add(guild)
    await db.commit()
    # Refresh guild so we can get the id.
    await db.refresh(guild)

    # Return the guild.
    return {
        "result": True,
        "message": "guild created successfully.",
        "guild": guild.serialize,
    }
