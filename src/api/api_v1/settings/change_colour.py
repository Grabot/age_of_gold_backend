"""Endpoint for changing username."""

from typing import Dict, Tuple

from fastapi import Depends, Security
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models.user import User
from src.models.user_token import UserToken
from src.util.decorators import handle_db_errors
from src.util.gold_logging import logger
from src.util.security import checked_auth_token
from src.util.rest_util import update_user_field


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

    me.colour = change_colour_request.new_colour
    await update_user_field(
        db, me, "username", change_colour_request.new_colour, "username_updated"
    )

    logger.info("User %s changed their colour", me.username)
    return {
        "success": True,
    }
