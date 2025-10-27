"""Endpoint for user logout."""

from typing import Any, Tuple

from fastapi import Depends, Response, Security
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models.user import User
from src.models.user_token import UserToken
from src.util.decorators import handle_db_errors
from src.util.gold_logging import logger
from src.util.security import checked_auth_token


@api_router_v1.post("/logout", status_code=200, response_model=dict)
@handle_db_errors("Logout failed")
async def logout_user(
    response: Response,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Handle user logout request."""
    user, user_token = user_and_token
    await db.delete(user_token)
    await db.commit()
    logger.info("User %s logged out successfully", user.username)
    return {"result": True, "message": "User logged out successfully."}
