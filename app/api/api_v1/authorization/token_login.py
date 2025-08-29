from typing import Any

from fastapi import Depends, Response, status
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession  # pyright: ignore[reportMissingImports]

from app.api.api_v1 import api_router_v1
from app.database import get_db
from app.util.gold_logging import logger
from app.util.util import check_token, get_failed_response, get_user_tokens


class LoginTokenRequest(BaseModel):
    access_token: str

    # TODO: Test this way, if works add to all endpoints?
    # @field_validator('access_token')
    # def check_empty(cls, v):
    #     if not v:
    #         raise ValueError("Access token is required")
    #     return v


@api_router_v1.post("/login/token", status_code=200)
async def login_token_user(
    login_token_request: LoginTokenRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    if not login_token_request.access_token:
        logger.warning("Token login failed: Invalid request")
        return get_failed_response(
            "Invalid request", response, status.HTTP_400_BAD_REQUEST
        )

    try:
        user, user_token = await check_token(db, login_token_request.access_token)
        if not user:
            return get_failed_response(
                "Invalid or expired token", response, status.HTTP_401_UNAUTHORIZED
            )

        return_user = user.serialize
        user_token = get_user_tokens(user)
        db.add(user_token)
        await db.commit()

        login_response = {
            "result": True,
            "message": "User logged in successfully.",
            "access_token": user_token.access_token,
            "refresh_token": user_token.refresh_token,
            "user": return_user,
        }
        return login_response

    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Database constraint violation: {e}")
        return get_failed_response(
            "Internal server error", response, status.HTTP_400_BAD_REQUEST
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Database error: {e}")
        return get_failed_response(
            "Internal server error", response, status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error during registration: {e}")
        return get_failed_response(
            "Internal server error", response, status.HTTP_500_INTERNAL_SERVER_ERROR
        )
