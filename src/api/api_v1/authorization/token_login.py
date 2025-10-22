"""Endpoint for token-based login."""

from typing import Any

from fastapi import Depends, Request, Response, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession  # pyright: ignore[reportMissingImports]

from src.api.api_v1 import api_router_v1
from src.database import get_db
from src.util.gold_logging import logger
from src.util.util import (
    check_token,
    get_auth_token,
    get_failed_response,
    get_user_tokens,
)


@api_router_v1.post("/login/token", status_code=200)
async def login_token_user(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Handle token-based login request."""
    auth_token = get_auth_token(request.headers.get("Authorization"))
    if auth_token == "":
        return get_failed_response(
            "Authorization token is missing or invalid",
            response,
            status.HTTP_400_BAD_REQUEST,
        )

    try:
        user, user_token_old = await check_token(db, auth_token)
        if not user:
            return get_failed_response(
                "Invalid or expired token", response, status.HTTP_401_UNAUTHORIZED
            )

        user_token_new = get_user_tokens(user)
        await db.delete(user_token_old)
        db.add(user_token_new)
        await db.commit()

        login_response = {
            "result": True,
            "access_token": user_token_new.access_token,
            "refresh_token": user_token_new.refresh_token,
        }
        return login_response

    except IntegrityError as e:
        logger.error("Database constraint violation: %s", e)
    except SQLAlchemyError as e:
        logger.error("Database error: %s", e)
    except Exception as e:
        logger.error("Unexpected error during registration: %s", e)

    await db.rollback()
    return get_failed_response(
        "Internal server error", response, status.HTTP_500_INTERNAL_SERVER_ERROR
    )
