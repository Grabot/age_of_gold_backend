import base64
import io
import os
import stat
from typing import Optional

from fastapi import Depends, Request, Response
from PIL import Image
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.api_v1 import api_router_v1
from app.api.rest_util import get_failed_response
from app.config.config import settings
from app.database import get_db
from app.models import User
from app.models.guild import Guild
from app.util.util import check_token, get_auth_token


class CreateGuildRequest(BaseModel):
    user_id: int
    guild_name: str
    guild_crest: Optional[str] = None


@api_router_v1.post("/guild/create", status_code=200)
async def create_guild(
    create_guild_request: CreateGuildRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    print("start guild create")
    user_id = create_guild_request.user_id
    guild_name = create_guild_request.guild_name
    guild_crest = create_guild_request.guild_crest

    auth_token = get_auth_token(request.headers.get("Authorization"))

    if auth_token == "":
        get_failed_response("An error occurred", response)

    user: Optional[User] = await check_token(db, auth_token)
    if not user:
        get_failed_response("An error occurred", response)

    statement_guild_name = select(Guild).where(func.lower(Guild.guild_name) == guild_name.lower())
    results_guild_name = await db.execute(statement_guild_name)
    result_guild_name = results_guild_name.first()

    print(f"results: {result_guild_name}")
    if result_guild_name is not None:
        return get_failed_response(
            "Guild name is already taken, please choose a different one.", response
        )

    member_rank = [user_id, 0]

    crest_default = True
    if guild_crest is not None:
        crest_default = False
    guild = Guild(
        user_id=user_id,
        guild_name=guild_name,
        member_ids=[member_rank],
        default_crest=crest_default,
    )
    db.add(guild)

    await db.commit()
    # Refresh guild so we can get the id.
    await db.refresh(guild)

    if guild_crest is not None:
        guild_crest_image = Image.open(io.BytesIO(base64.b64decode(guild_crest)))
        # Get the file name and path
        file_folder = settings.UPLOAD_FOLDER_CRESTS
        file_name = guild.crest_filename()
        # Store the image under the same hash but without the "default".
        file_path = os.path.join(file_folder, "%s.png" % file_name)
        guild_crest_image.save(file_path)
        os.chmod(file_path, stat.S_IRWXO)

    # Return the guild without the crest because it's present at the client. Only send id.
    return {
        "result": True,
        "message": f"{guild.id}",
    }
