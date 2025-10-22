"""Endpoint for user logout."""

from typing import Any

from fastapi import Depends, Request, Response, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession  # pyright: ignore[reportMissingImports]

from src.api.api_v1 import api_router_v1
from src.database import get_db
from src.util.gold_logging import logger
from src.util.util import check_token, get_auth_token, get_failed_response


@api_router_v1.post("/logout", status_code=200, response_model=dict)
async def logout_user(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Handle user logout request."""
    auth_token = get_auth_token(request.headers.get("Authorization"))
    if auth_token == "":
        return get_failed_response(
            "Authorization token is missing or invalid",
            response,
            status.HTTP_401_UNAUTHORIZED,
        )

    try:
        user, user_token = await check_token(db, auth_token)
        if not user:
            return get_failed_response(
                "User not found or token expired",
                response,
                status.HTTP_401_UNAUTHORIZED,
            )

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
