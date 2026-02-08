"""Endpoints for sending and fetching messages."""

from typing import Any, Dict, Tuple

from fastapi import Depends, HTTPException, Security, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.selectable import Select
from sqlmodel import select

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models.chat import Chat
from src.models.message import Message
from src.models.user import User
from src.models.user_token import UserToken
from src.sockets.sockets import sio
from src.util.decorators import handle_db_errors
from src.util.security import checked_auth_token
from src.util.util import get_group_room


class SendMessageRequest(BaseModel):
    """Request model for sending a message."""

    chat_id: int
    content: str
    message_type: int = 0


@api_router_v1.post("/message/send", status_code=200)
@handle_db_errors("Sending message failed")
async def send_message(
    send_message_request: SendMessageRequest,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Handle send message request via HTTP API.

    This endpoint allows sending messages via HTTP in addition to WebSocket.
    The message is saved to the database and broadcasted to all chat members.
    """
    user, _ = user_and_token
    chat_id = send_message_request.chat_id
    content = send_message_request.content
    message_type = send_message_request.message_type

    if user.id is None:
        raise HTTPException(status_code=400, detail="User ID not found")

    sender_id = user.id

    # Verify user is in the chat
    chat_statement: Select = (
        select(Chat).where(Chat.id == chat_id).options(selectinload(Chat.groups))  # type: ignore
    )
    chat: Chat = (await db.execute(chat_statement)).scalar_one()

    if sender_id not in chat.user_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of this chat",
        )

    # Create and save the message
    message = Message(
        chat_id=chat_id,
        sender_id=sender_id,
        content=content,
        message_type=message_type,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)

    # Increment chat message version
    for group in chat.groups:
        group.group_version += 1
        db.add(group)
    chat.current_message_id = message.id
    await db.commit()

    # Prepare message data for broadcasting
    message_data = {
        "id": message.id,
        "chat_id": message.chat_id,
        "sender_id": message.sender_id,
        "content": message.content,
        "created_at": message.created_at.isoformat() if message.created_at else None,
        "message_type": message.message_type,
    }

    group_room = get_group_room(chat_id)
    await sio.emit(
        "message_received",
        message_data,
        room=group_room,
    )

    return {"success": True, "data": message_data}

