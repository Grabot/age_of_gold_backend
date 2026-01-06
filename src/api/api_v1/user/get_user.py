"""Endpoint for getting a user."""

from typing import Any, Dict, Optional, Tuple

from fastapi import Depends, Security, Body
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models.user import User
from src.models.user_token import UserToken
from src.util.decorators import handle_db_errors
from src.util.security import checked_auth_token
from src.util.rest_util import get_user_from_db


class GetUserRequest(BaseModel):
    """Request model for getting a user."""

    user_id: Optional[int]


@api_router_v1.post("/user/get", status_code=200, response_model=dict)
@handle_db_errors("Getting a user failed")
async def get_user(
    get_user_request: Optional[GetUserRequest] = Body(default=None),
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, bool | Dict[str, Any]]:
    """Handle get user request."""
    user, _ = user_and_token
    if not get_user_request or not get_user_request.user_id:
        return {"success": True, "data": {"user": user.serialize}}

    got_user = await get_user_from_db(db, get_user_request.user_id)
    if got_user is None:
        return {"success": False}

    return {"success": True, "data": got_user.serialize}
