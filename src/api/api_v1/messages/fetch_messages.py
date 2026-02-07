"""Endpoints for sending and fetching messages."""

from typing import Any, Dict, List, Optional, Tuple

from fastapi import Depends, HTTPException, Security, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Select
from sqlmodel import select

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models.chat import Chat
from src.models.message import Message
from src.models.user import User
from src.models.user_token import UserToken
from src.util.decorators import handle_db_errors
from src.util.security import checked_auth_token


class FetchMessagesRequest(BaseModel):
    """Request model for fetching messages from a specific message_id onwards."""

    chat_id: int
    from_message_id: Optional[int] = None


@api_router_v1.post("/message/fetch", status_code=200)
@handle_db_errors("Fetching messages failed")
async def fetch_messages(
    fetch_messages_request: FetchMessagesRequest,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Handle fetch messages request.

    Fetches messages from a chat starting from a specific message_id.
    If from_message_id is not provided, fetches the most recent messages.
    """
    user, _ = user_and_token
    chat_id = fetch_messages_request.chat_id
    from_message_id = fetch_messages_request.from_message_id

    if user.id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User ID not found")

    user_id = user.id

    # Verify user is in the chat
    chat: Chat = (await db.execute(select(Chat).where(Chat.id == chat_id))).scalar_one()

    if user_id not in chat.user_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of this chat",
        )

    # Build the query
    messages_statement: Select = select(Message).where(Message.chat_id == chat_id)

    # If from_message_id is provided, fetch messages from that ID onwards
    if from_message_id is not None:
        messages_statement = messages_statement.where(Message.id >= from_message_id)

    # Order by id (chronological order) and limit results
    messages_statement = messages_statement.order_by(Message.id)

    messages_result = await db.execute(messages_statement)
    messages = messages_result.scalars().all()

    # Serialize messages
    messages_data: List[Dict[str, Any]] = [
        {
            "id": msg.id,
            "chat_id": msg.chat_id,
            "sender_id": msg.sender_id,
            "content": msg.content,
            "created_at": msg.created_at.isoformat() if msg.created_at else None,
            "message_type": msg.message_type,
        }
        for msg in messages
    ]

    return {
        "success": True,
        "data": {
            "chat_id": chat_id,
            "messages": messages_data,
        },
    }

