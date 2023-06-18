from typing import Optional

from fastapi import Depends, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.api_v1 import api_router_v1
from app.api.rest_util import get_failed_response
from app.database import get_db
from app.models import User
from app.util.util import check_token


class PasswordUpdateRequest(BaseModel):
    access_token: str
    new_password: str


@api_router_v1.post("/password/update", status_code=200)
async def update_password(
    password_update_request: PasswordUpdateRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    user: Optional[User] = await check_token(db, password_update_request.access_token, False)
    if not user:
        return get_failed_response("user not found", response)

    new_password = password_update_request.new_password
    user.hash_password(new_password)
    db.add(user)
    await db.commit()

    return {
        "result": True,
        "message": "password updated!",
    }
