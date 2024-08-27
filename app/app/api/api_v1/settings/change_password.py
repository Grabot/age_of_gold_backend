from typing import Optional

from fastapi import Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.api_v1 import api_router_v1
from app.util.rest_util import get_failed_response
from app.database import get_db
from app.models import User
from app.util.util import check_token, get_auth_token


class ChangePasswordRequest(BaseModel):
    password: str


@api_router_v1.post("/change/password", status_code=200)
async def change_password(
    change_password_request: ChangePasswordRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    print("change password")
    auth_token = get_auth_token(request.headers.get("Authorization"))

    if auth_token == "":
        return get_failed_response("An error occurred", response)

    user: Optional[User] = await check_token(db, auth_token)
    if not user:
        return get_failed_response("An error occurred", response)

    new_password = change_password_request.password
    user.hash_password(new_password)

    db.add(user)
    await db.commit()

    return {
        "result": True,
        "message": new_password,
    }
