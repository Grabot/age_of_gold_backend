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


class ChangeUsernameRequest(BaseModel):
    """Request model for changing username."""

    new_username: str


@api_router_v1.patch("/user/username", status_code=200, response_model=Dict)
@handle_db_errors("Changing username failed")
async def change_username(
    change_username_request: ChangeUsernameRequest,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, bool]:
    """Handle change username request."""
    user, _ = user_and_token
    user.username = change_username_request.new_username
    user.profile_version += 1
    db.add(user)
    await db.commit()
    logger.info("User %s changed their username", user.username)
    return {
        "success": True,
    }
