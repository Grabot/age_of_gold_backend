from fastapi import Depends, Request
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from util.util import check_token, get_auth_token

from app.api.api_v1 import api_router_v1
from app.database import get_db
from app.models.message import GlobalMessage


def get_failed_response_messages():
    return {"items": [], "total": 0, "page": 1, "size": 1, "pages": 0}


@api_router_v1.get("/get/message/global", response_model=Page[GlobalMessage], status_code=200)
async def get_global_message(request: Request, db: AsyncSession = Depends(get_db)):
    print(f"header {request}")
    auth_token = get_auth_token(request.headers.get("Authorization"))
    print(f"token {auth_token}")
    if auth_token == "":
        get_failed_response_messages()

    user = await check_token(db, auth_token)
    if not user:
        get_failed_response_messages()

    return await paginate(db, select(GlobalMessage).order_by(desc(GlobalMessage.timestamp)))
