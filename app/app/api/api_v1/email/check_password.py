from fastapi import Depends, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from util.util import check_token

from app.api.api_v1 import api_router_v1
from app.api.rest_util import get_failed_response
from app.database import get_db


class PasswordCheckRequest(BaseModel):
    access_token: str


@api_router_v1.post("/password/check", status_code=200)
async def check_password(
    password_check_request: PasswordCheckRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    user = await check_token(db, password_check_request.access_token, False)
    if not user:
        return get_failed_response("user not found", response)

    return {
        "result": True,
        "message": "password check was good",
    }
