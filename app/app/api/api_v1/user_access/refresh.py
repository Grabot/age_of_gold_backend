from fastapi import Depends, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.api_v1 import api_router_v1
from app.api.rest_util import get_failed_response
from app.database import get_db
from app.util.util import get_user_tokens, refresh_user_token


class RefreshRequest(BaseModel):
    access_token: str
    refresh_token: str


@api_router_v1.post("/refresh", status_code=200)
async def refresh_user(
    refresh_request: RefreshRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    access_token = refresh_request.access_token
    refresh_token = refresh_request.refresh_token

    user = await refresh_user_token(db, access_token, refresh_token)
    if not user:
        return get_failed_response("An error occurred", response)

    user_token = get_user_tokens(user)
    db.add(user_token)
    await db.commit()

    login_response = {
        "result": True,
        "message": "user logged in successfully.",
        "access_token": user_token.access_token,
        "refresh_token": user_token.refresh_token,
        "user": user.serialize,
    }

    return login_response
