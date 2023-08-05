from fastapi import Depends, Request
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic import BaseModel
from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.api_v1 import api_router_v1
from app.database import get_db
from app.models import User
from app.models.message import PersonalMessage
from app.util.util import check_token, get_auth_token


def get_failed_response_messages():
    return {"items": [], "total": 0, "page": 1, "size": 1, "pages": 0}


class GetMessagePersonalRequest(BaseModel):
    user_get_id: int


@api_router_v1.post("/get/message/personal", response_model=Page[PersonalMessage], status_code=200)
async def get_personal_message(
    request: Request,
    get_message_personal_request: GetMessagePersonalRequest,
    db: AsyncSession = Depends(get_db),
):
    auth_token = get_auth_token(request.headers.get("Authorization"))
    if auth_token == "":
        return get_failed_response_messages()

    user_request = await check_token(db, auth_token)
    if not user_request:
        return get_failed_response_messages()

    get_user_id = get_message_personal_request.user_get_id
    user_statement = select(User).filter_by(id=get_user_id)
    results = await db.execute(user_statement)
    result = results.first()
    if result is None:
        return None
    user_get = result.User

    return await paginate(
        db,
        (
            select(PersonalMessage)
            .filter_by(user_id=user_request.id, receiver_id=user_get.id)
            .union(
                select(PersonalMessage).filter_by(user_id=user_get.id, receiver_id=user_request.id)
            )
        ).order_by(desc(PersonalMessage.timestamp)),
    )
