"""Endpoint for getting a user."""

from typing import Any, Dict, Tuple

from fastapi import Depends, Security
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models.user import User
from src.models.user_token import UserToken
from src.util.decorators import handle_db_errors
from src.util.gold_logging import logger
from src.util.security import checked_auth_token


class GetUserRequest(BaseModel):
    """Request model for getting a user."""

    user_id: int


@api_router_v1.post("/user/get", status_code=200, response_model=dict)
@handle_db_errors("Getting a user failed")
async def get_user(
    get_user_request: GetUserRequest,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, bool | Dict[str, Any]]:
    """Handle get user request."""
    user, _ = user_and_token
    user_statement = select(User).where(
        func.lower(User.id) == get_user_request.user_id
    )
    results_user = await db.execute(user_statement)
    result_user = results_user.first()
    if result_user is None:
        return {"success": False}

    got_user: User = result_user.User
    logger.info(
        "User %s got user %s",
        user.username,
        got_user.username,
    )
    return {"success": True, "data": got_user.serialize}
