"""Endpoint for user logout."""

from typing import Any

from fastapi import Depends, Response, Security, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1 import api_router_v1
from src.database import get_db
from src.util.gold_logging import logger
from src.util.security import checked_auth_token
from src.util.util import get_failed_response


@api_router_v1.post("/logout", status_code=200, response_model=dict)
async def logout_user(
    response: Response,
    user_and_token=Security(checked_auth_token, scopes=["user"]),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Handle user logout request."""
    try:
        user, user_token = user_and_token
        await db.delete(user_token)
        await db.commit()
        logger.info("User %s logged out successfully", user.username)
        return {"result": True, "message": "User logged out successfully."}
    except SQLAlchemyError as e:
        logger.error("Database error during logout: %s", e)
    except Exception as e:
        logger.error("Unexpected error during logout: %s", e)

    await db.rollback()
    return get_failed_response(
        "Internal server error", response, status.HTTP_500_INTERNAL_SERVER_ERROR
    )
