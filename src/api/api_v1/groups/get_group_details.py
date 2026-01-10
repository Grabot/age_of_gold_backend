"""Endpoint for getting group details."""

from typing import Any, Dict, Tuple

from fastapi import Depends, HTTPException, Security
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models.chat import Chat
from src.models.group import Group
from src.models.user import User
from src.models.user_token import UserToken
from src.util.security import checked_auth_token


class GetGroupDetailsRequest(BaseModel):
    """Request model for getting group details."""

    group_id: int


@api_router_v1.post("/group/details", status_code=200)
async def get_group_details(
    get_group_details_request: GetGroupDetailsRequest,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Handle get group details request."""
    me, _ = user_and_token

    if me.id is None:
        raise HTTPException(status_code=400, detail="Can't find user")

    group_id = get_group_details_request.group_id

    # Check if user is a member of this group
    group_statement = select(Group).where(
        Group.user_id == me.id, Group.group_id == group_id
    )
    group_result = await db.execute(group_statement)
    group_entry = group_result.first()

    if not group_entry:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this group",
        )

    # Get the chat object
    chat_statement = select(Chat).where(Chat.id == group_id)
    chat_result = await db.execute(chat_statement)
    chat_entry = chat_result.first()

    if not chat_entry:
        raise HTTPException(
            status_code=404,
            detail="Group not found",
        )

    chat: Chat = chat_entry.Chat
    chat_data = chat.serialize()  # type: ignore[attr-defined]

    return {
        "success": True,
        "data": chat_data,
    }
