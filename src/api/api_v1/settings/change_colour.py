"""Endpoint for changing username."""

from typing import Dict, Tuple

from fastapi import Depends, Security, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models.user import User
from src.models.user_token import UserToken
from src.util.decorators import handle_db_errors
from src.util.gold_logging import logger
from src.util.security import checked_auth_token
from src.util.rest_util import update_friend_versions_and_notify


class ChangeColourRequest(BaseModel):
    """Request model for changing colour."""

    new_colour: str


@api_router_v1.patch("/user/colour", status_code=200, response_model=Dict)
@handle_db_errors("Changing colour failed")
async def change_colour(
    change_colour_request: ChangeColourRequest,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, bool]:
    """Handle change colour request."""
    me, _ = user_and_token

    if me.id is None:
        raise HTTPException(status_code=400, detail="Can't find user")

    me.colour = change_colour_request.new_colour
    me.profile_version += 1
    db.add(me)

    await update_friend_versions_and_notify(
        db,
        me.id,
        "colour_updated",
        {
            "user_id": me.id,
            "new_colour": me.colour,
            "profile_version": me.profile_version,
        },
    )

    await db.commit()
    logger.info("User %s changed their colour", me.username)
    return {
        "success": True,
    }
