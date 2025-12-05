"""Endpoint for resetting password."""

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
from src.util.util import hash_password


class ResetPasswordRequest(BaseModel):
    """Request model for resetting password."""

    new_password: str


@api_router_v1.patch("/password/reset", status_code=200, response_model=Dict)
@handle_db_errors("Resetting password failed")
async def reset_password(
    reset_password_request: ResetPasswordRequest,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, bool]:
    """Handle reset password request."""
    user, _ = user_and_token
    user.password_hash = hash_password(reset_password_request.new_password + user.salt)
    db.add(user)
    await db.commit()
    logger.info("User %s changed their password", user.username)
    return {
        "success": True,
    }
