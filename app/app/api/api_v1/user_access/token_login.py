from fastapi import Depends, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.api_v1 import api_router_v1
from app.util.rest_util import get_failed_response
from app.database import get_db
from app.util.util import check_token, get_user_tokens


class LoginTokenRequest(BaseModel):
    access_token: str


@api_router_v1.post("/login/token", status_code=200)
async def login_token_user(
    login_token_request: LoginTokenRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    user = await check_token(db, login_token_request.access_token, True)

    if not user:
        return get_failed_response("user not found", response)

    return_user = user.serialize
    user_token = get_user_tokens(user)
    db.add(user_token)
    await db.commit()
    # We don't refresh the user object because we know all we want to know
    login_response = {
        "result": True,
        "message": "user logged in successfully.",
        "access_token": user_token.access_token,
        "refresh_token": user_token.refresh_token,
        "user": return_user,
    }

    return login_response
