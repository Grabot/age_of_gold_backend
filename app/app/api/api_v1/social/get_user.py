from typing import Optional

from fastapi import Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.api_v1 import api_router_v1

from app.database import get_db
from app.models import User
from app.util.util import check_token, get_auth_token
from app.util.rest_util import get_failed_response


class GetUserRequest(BaseModel):
    username: str


@api_router_v1.post("/get/user", status_code=200)
async def get_user(
    get_user_request: GetUserRequest,
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

    search_name = get_user_request.username
    user_statement = select(User).where(func.lower(User.username) == search_name.lower())
    results = await db.execute(user_statement)
    result = results.first()
    if result is None:
        return get_failed_response("User not found", response)
    search_user = result.User

    return {"result": True, "user": search_user.serialize_get}
