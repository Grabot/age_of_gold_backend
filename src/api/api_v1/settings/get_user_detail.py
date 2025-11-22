"""Endpoint for getting user detail."""

from typing import Any, Tuple, Dict

from fastapi import Depends, Security
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models.user import User
from src.models.user_token import UserToken
from src.util.decorators import handle_db_errors
from src.util.gold_logging import logger
from src.util.security import checked_auth_token


@api_router_v1.get("/user/detail", status_code=200, response_model=dict)
@handle_db_errors("Get user detail failed")
async def get_user_detail(
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, bool | Dict[str, Any]]:
    """Handle get user detail request."""
    user, _ = user_and_token
    logger.info("User %s got their user detail", user.username)
    return {"success": True, "data": {"user": user.serialize}}
