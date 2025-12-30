"""Endpoint for searching for friend."""

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


class SearchFriendRequest(BaseModel):
    """Request model for searching friend."""

    username: str


@api_router_v1.post("/friend/search", status_code=200, response_model=dict)
@handle_db_errors("Searching friend failed")
async def search_friend(
    search_friend_request: SearchFriendRequest,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, bool | Dict[str, Any]]:
    """Handle search friend request."""
    user, _ = user_and_token
    user_statement = select(User).where(
        func.lower(User.username) == search_friend_request.username.lower()
    )
    results_user = await db.execute(user_statement)
    result_user = results_user.first()
    if result_user is None:
        return {"success": False}

    searched_user: User = result_user.User
    logger.info(
        "User %s searched for potential friend %s",
        user.username,
        searched_user.username,
    )
    return {"success": True, "data": searched_user.serialize}
