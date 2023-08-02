from typing import Optional

from fastapi import Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.api_v1 import api_router_v1
from app.api.rest_util import get_failed_response
from app.database import get_db
from app.models import User
from app.util.util import check_token, get_auth_token


class SearchFriendRequest(BaseModel):
    username: str


@api_router_v1.post("/search/friend", status_code=200)
async def search_friend(
    search_friend_request: SearchFriendRequest,
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

    user_name = search_friend_request.username
    user_statement = select(User).where(func.lower(User.username) == user_name.lower())
    results = await db.execute(user_statement)
    result = results.first()

    if not result:
        return get_failed_response("an error occurred", response)
    search_user: User = result.User

    return {"result": True, "friend": search_user.serialize_get}
