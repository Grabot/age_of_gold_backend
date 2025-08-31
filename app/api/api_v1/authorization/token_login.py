from typing import Any

from fastapi import Depends, Request, Response, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession  # pyright: ignore[reportMissingImports]

from app.api.api_v1 import api_router_v1
from app.database import get_db
from app.util.gold_logging import logger
from app.util.util import (  # pylint: disable=redefined-builtin
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
    auth_token = get_auth_token(request.headers.get("Authorization"))
    if auth_token == "":
        return get_failed_response(
            "Authorization token is missing or invalid",
            response,
            status.HTTP_401_UNAUTHORIZED,
        )

    try:
        user, user_token_old = await check_token(db, auth_token)
        if not user:
            return get_failed_response(
                "Invalid or expired token", response, status.HTTP_401_UNAUTHORIZED
            )

        return_user = user.serialize
        user_token_new = get_user_tokens(user)
        await db.delete(user_token_old)
        db.add(user_token_new)
        await db.commit()

        login_response = {
            "result": True,
            "message": "User logged in successfully.",
            "access_token": user_token_new.access_token,
            "refresh_token": user_token_new.refresh_token,
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
