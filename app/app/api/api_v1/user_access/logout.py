from typing import Optional

from fastapi import Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.api_v1 import api_router_v1
from app.api.rest_util import get_failed_response
from app.database import get_db
from app.models import User, UserToken
from app.util.util import check_token, get_auth_token


@api_router_v1.post("/logout", status_code=200)
async def logout_user(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    auth_token = get_auth_token(request.headers.get("Authorization"))
    if auth_token == "":
        return get_failed_response("An error occurred", response)

    user: Optional[User] = await check_token(db, auth_token)
    if not user:
        return get_failed_response("An error occurred", response)

    token_statement = select(UserToken).filter_by(access_token=auth_token)
    results_token = await db.execute(token_statement)
    result_token = results_token.first()
    if result_token is None:
        return get_failed_response("An error occurred", response)

    user_token = result_token.UserToken
    await db.delete(user_token)
    await db.commit()

    return {
        "result": True,
        "message": "user logged out successfully.",
    }
