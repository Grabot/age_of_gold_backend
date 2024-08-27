from typing import List, Optional

from fastapi import Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.api_v1 import api_router_v1
from app.util.rest_util import get_failed_response
from app.database import get_db
from app.models import User
from app.util.util import check_token, get_auth_token


class GetAvatarsRequest(BaseModel):
    avatars: List[int]


@api_router_v1.post("/get/avatars", status_code=200)
async def get_avatars(
    get_avatars_request: GetAvatarsRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    auth_token = get_auth_token(request.headers.get("Authorization"))

    if auth_token == "":
        return get_failed_response("An error occurred", response)

    user_request: Optional[User] = await check_token(db, auth_token)
    if not user_request:
        return get_failed_response("An error occurred", response)

    print(f"going to filter the following list of avatars: {get_avatars_request.avatars}")
    statement_hexes = select(User).filter(User.id.in_(get_avatars_request.avatars))
    results = await db.execute(statement_hexes)
    users = results.all()
    avatars = []
    for use in users:
        user = use.User
        avatars.append(user.serialize_get)
    return {"result": True, "avatars": avatars}
