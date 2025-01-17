from typing import Optional

from fastapi import Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, update

from app.api.api_v1 import api_router_v1
from app.util.rest_util import get_failed_response
from app.database import get_db
from app.models import User
from app.models.message import GlobalMessage
from app.util.util import check_token, get_auth_token


class ChangeUsernameRequest(BaseModel):
    username: str


@api_router_v1.post("/change/username", status_code=200)
async def change_username(
    change_username_request: ChangeUsernameRequest,
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

    new_username = change_username_request.username
    user_statement = select(User).where(func.lower(User.username) == new_username.lower())
    results = await db.execute(user_statement)
    result = results.first()
    if result is not None:
        return get_failed_response(
            "User is already taken, please choose a different one.", response
        )

    user.set_new_username(new_username)
    # update global messages

    message_update_statement = (
        update(GlobalMessage)
        .values(sender_name=new_username)
        .where(GlobalMessage.sender_id == user.id)
    )
    results = await db.execute(message_update_statement)

    db.add(user)
    await db.commit()

    return {
        "result": True,
        "message": new_username,
    }

