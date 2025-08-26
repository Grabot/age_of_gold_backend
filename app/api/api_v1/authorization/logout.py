from typing import Any

from fastapi import Depends, Request, Response, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession  # pyright: ignore[reportMissingImports]
from sqlmodel import select

from app.api.api_v1 import api_router_v1
from app.database import get_db
from app.models import UserToken
from app.util.gold_logging import logger
from app.util.util import check_token, get_auth_token, get_failed_response


@api_router_v1.post("/logout", status_code=200, response_model=dict)
async def logout_user(
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

    user = await check_token(db, auth_token)
    if not user:
        return get_failed_response(
            "User not found or token expired", response, status.HTTP_401_UNAUTHORIZED
        )

    token_statement = select(UserToken).filter_by(access_token=auth_token)  # type: ignore
    results_token = await db.execute(token_statement)
    result_token = results_token.first()

    if result_token is None:
        return get_failed_response(
            "Authorization token is missing or invalid",
            response,
            status.HTTP_404_NOT_FOUND,
        )

    try:
        await db.delete(result_token.UserToken)
        await db.commit()
        logger.info(f"User {user.id} logged out successfully")
        return {"result": True, "message": "User logged out successfully."}
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Database error during logout: {e}")
        return get_failed_response(
            "Internal server error", response, status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error during logout: {e}")
        return get_failed_response(
            "Internal server error", response, status.HTTP_500_INTERNAL_SERVER_ERROR
        )
