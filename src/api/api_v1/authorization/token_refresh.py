"""endpoint for token refresh"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models import User
from src.util.decorators import handle_db_errors
from src.util.gold_logging import logger
from src.util.security import decode_token
from src.util.util import (
    SuccessfulLoginResponse,
    get_successful_login_response,
    get_user_tokens,
    refresh_user_token,
)


class RefreshRequest(BaseModel):
    """Request model for token refresh."""

    access_token: str
    refresh_token: str


@api_router_v1.post("/login/token/refresh", status_code=200)
@handle_db_errors("Token refresh failed")
async def refresh_user(
    refresh_request: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> SuccessfulLoginResponse:
    """Handle token refresh request."""
    if not refresh_request.access_token or not refresh_request.refresh_token:
        logger.warning("Refresh failed: Invalid request")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request"
        )
    user: Optional[User] = await refresh_user_token(
        db, refresh_request.access_token, refresh_request.refresh_token
    )
    if not user or not decode_token(refresh_request.refresh_token, "refresh"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired tokens"
        )
    user_token = get_user_tokens(user)
    db.add(user_token)
    await db.commit()
    return await get_successful_login_response(user_token, user, db)
