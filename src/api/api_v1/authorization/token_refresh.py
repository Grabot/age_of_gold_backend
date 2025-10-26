"""endpoint for token refresh"""

from typing import Any, Optional

from fastapi import Depends, Response, Security, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1 import api_router_v1
from src.database import get_db
from src.models import User
from src.util.decorators import handle_db_errors
from src.util.gold_logging import logger
from src.util.security import decode_token, get_valid_auth_token
from src.util.util import (
    get_failed_response,
    get_successful_user_response,
    get_user_tokens,
    refresh_user_token,
)


class RefreshRequest(BaseModel):
    """Request model for token refresh."""

    refresh_token: str


@api_router_v1.post("/login/token/refresh", status_code=200)
@handle_db_errors("Token refresh failed")
async def refresh_user(
    refresh_request: RefreshRequest,
    response: Response,
    access_token: str = Security(get_valid_auth_token, scopes=["user"]),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Handle token refresh request."""
    if not refresh_request.refresh_token:
        logger.warning("Refresh failed: Invalid request")
        return get_failed_response(
            "Invalid request", response, status.HTTP_400_BAD_REQUEST
        )
    user: Optional[User] = await refresh_user_token(
        db, access_token, refresh_request.refresh_token
    )
    if not user or not decode_token(refresh_request.refresh_token, "refresh"):
        return get_failed_response(
            "Invalid or expired tokens", response, status.HTTP_401_UNAUTHORIZED
        )
    user_token = get_user_tokens(user)
    db.add(user_token)
    await db.commit()
    return get_successful_user_response(user, user_token)
