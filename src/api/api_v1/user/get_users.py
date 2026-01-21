"""Endpoint for getting multiple users."""

from typing import Any, Dict, List, Tuple

from fastapi import Depends, Security
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Select
from sqlmodel import select

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models.user import User
from src.models.user_token import UserToken
from src.util.decorators import handle_db_errors
from src.util.gold_logging import logger
from src.util.security import checked_auth_token


class GetUsersRequest(BaseModel):
    """Request model for getting multiple users."""

    user_ids: List[int]


@api_router_v1.post("/users", status_code=200)
@handle_db_errors("Getting multiple users failed")
async def get_multiple_users(
    get_users_request: GetUsersRequest,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Handle get multiple users request."""
    user, _ = user_and_token

    if not get_users_request.user_ids:
        return {"success": False, "message": "No user IDs provided"}

    user_statement: Select = select(User).where(
        User.id.in_(get_users_request.user_ids)
    )
    results_users = await db.execute(user_statement)
    found_users = results_users.scalars().all()
    if not found_users:
        return {"success": False, "message": "No users found"}

    # Serialize found users
    users_data = [user.serialize for user in found_users]

    logger.info(
        "User %s retrieved %d users",
        user.username,
        len(users_data),
    )

    return {"success": True, "data": users_data}
