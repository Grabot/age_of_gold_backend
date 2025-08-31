from typing import Any, Optional

from fastapi import Depends, Request, Response, status
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession  # pyright: ignore[reportMissingImports]

from app.api.api_v1 import api_router_v1
from app.database import get_db
from app.models import User
from app.util.gold_logging import logger
from app.util.util import (
    get_auth_token,
    get_failed_response,
    get_user_tokens,
    refresh_user_token,
)


class RefreshRequest(BaseModel):
    refresh_token: str


@api_router_v1.post("/refresh", status_code=200)
async def refresh_user(
    request: Request,
    refresh_request: RefreshRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    auth_token = get_auth_token(request.headers.get("Authorization"))
    if auth_token == "":
        return get_failed_response(
            "Authorization token is missing or invalid",
            response,
            status.HTTP_401_UNAUTHORIZED,
        )

    if not refresh_request.refresh_token:
        logger.warning("Refresh failed: Invalid request")
        return get_failed_response(
            "Invalid request", response, status.HTTP_400_BAD_REQUEST
        )

    try:
        user: Optional[User] = await refresh_user_token(
            db, auth_token, refresh_request.refresh_token
        )
        if not user:
            return get_failed_response(
                "Invalid or expired tokens", response, status.HTTP_401_UNAUTHORIZED
            )

        user_token = get_user_tokens(user)
        db.add(user_token)
        await db.commit()
        login_response = {
            "result": True,
            "message": "Tokens refreshed successfully.",
            "access_token": user_token.access_token,
            "refresh_token": user_token.refresh_token,
            "user": user.serialize,
        }
        return login_response

    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Database integrity error during registration: {e}")
        return get_failed_response(
            "Internal server error", response, status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Database error during token refresh: {e}")
        return get_failed_response(
            "Internal server error", response, status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error during token refresh: {e}")
        return get_failed_response(
            "Internal server error", response, status.HTTP_500_INTERNAL_SERVER_ERROR
        )
