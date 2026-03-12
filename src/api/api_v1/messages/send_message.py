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
from src.util.util import get_group_room, get_user_room


class SendMessageRequest(BaseModel):
    """Request model for sending a message."""

    chat_id: int
    content: str
    private: bool
    # TODO: Remove? For regular text always 0
    message_type: int


@api_router_v1.post("/message/send", status_code=200)
@handle_db_errors("Sending message failed")
async def send_message(
    send_message_request: SendMessageRequest,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Handle send message request."""
    user, _ = user_and_token
    chat_id = send_message_request.chat_id
    content = send_message_request.content
    private = send_message_request.private
    message_type = send_message_request.message_type

    if user.id is None:
        raise HTTPException(status_code=400, detail="User ID not found")

    sender_id = user.id

    # Verify user is in the chat
    chat_statement: Select = select(Chat).where(Chat.id == chat_id)
    if private:
        chat_statement = chat_statement.options(selectinload(Chat.friends))  # type: ignore
    else:
        chat_statement = chat_statement.options(selectinload(Chat.groups))  # type: ignore
    chat: Chat = (await db.execute(chat_statement)).scalar_one()

    if sender_id not in chat.user_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of this chat",
        )

    # Create and save the message
    message = Message(
        message_id=chat.current_message_id + 1,
        chat_id=chat_id,
        sender_id=sender_id,
        content=content,
        message_type=message_type,
        receive_remaining = [user_id for user_id in chat.user_ids if user_id != sender_id]
    )
    chat.current_message_id += 1
    db.add(message)
    db.add(chat)

    # Increment chat message version
    if private:
        for friend in chat.friends:
            if friend.user_id != sender_id:
                friend.unread_messages += 1
                db.add(friend)
    else:
        for group in chat.groups:
            if group.user_id != sender_id:
                group.unread_messages += 1
                db.add(group)
    await db.commit()

    # Prepare message data for broadcasting
    created_at_str = message.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    message_data = {
        "id": message.message_id,
        "chat_id": message.chat_id,
        "sender_id": message.sender_id,
        "content": message.content,
        "created_at": created_at_str,
        "message_type": message.message_type,
    }

    print("socket emit message")
    if private:
        for friend in chat.friends:
            if friend.user_id != sender_id:
                print("sending message to friend")
                friend_room = get_user_room(friend.user_id)
                await sio.emit(
                    "message_received",
                    message_data,
                    room=friend_room,
                )
    else:
        print("sending message to group")
        group_room = get_group_room(chat_id)
        await sio.emit(
            "message_received",
            message_data,
            room=group_room,
        )

    return {"success": True, "data": message.message_id}
