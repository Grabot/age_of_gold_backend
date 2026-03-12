"""Endpoints for sending and fetching messages."""

import uuid
import logging
from typing import Any, Dict, Tuple, Optional
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Security, status, Request, Form, File, UploadFile
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
from src.util.util import get_group_room, get_user_room, save_attachment
from src.util.gold_logging import logger


@api_router_v1.post("/message/send/attachment", status_code=200)
@handle_db_errors("Sending message failed")
async def send_message_attachment(
    request: Request,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
    chat_id: int = Form(...),
    content: str = Form(...),
    private: bool = Form(...),
    message_type: int = Form(...),
    message_data: Optional[UploadFile] = File(default=None),
) -> Dict[str, Any]:
    """Handle send message with attachment request.
    
    Args:
        request: FastAPI request object
        user_and_token: Authenticated user and token tuple
        db: Database session
        chat_id: ID of the chat
        content: Message content text
        private: Whether this is a private chat
        message_type: Type of message (0=text, 1=image, 2=video, etc.)
        message_data: Uploaded file data
        
    Returns:
        Dictionary with success status and message ID
        
    Raises:
        HTTPException: For various error conditions (validation, permissions, file handling)
    """
    user, _ = user_and_token

    s3_client = request.app.state.s3
    cipher = request.app.state.cipher

    logger.info(f"User {user.id} sending message to chat {chat_id}")

    # Input validation
    if user.id is None:
        logger.error("User ID not found in authenticated user")
        raise HTTPException(status_code=400, detail="User ID not found")

    if chat_id <= 0:
        logger.error(f"Invalid chat_id: {chat_id}")
        raise HTTPException(status_code=400, detail="Invalid chat ID")

    if not content and not message_data:
        logger.error("Both content and message_data are empty")
        raise HTTPException(status_code=400, detail="Message content or attachment required")

    if message_data and len(content) > 1000:
        logger.error("Content too long for attachment message")
        raise HTTPException(status_code=400, detail="Content too long for attachment message")

    sender_id = user.id

    # Verify user is in the chat
    try:
        chat_statement: Select = select(Chat).where(Chat.id == chat_id)
        if private:
            chat_statement = chat_statement.options(selectinload(Chat.friends))  # type: ignore
        else:
            chat_statement = chat_statement.options(selectinload(Chat.groups))  # type: ignore
        chat: Chat = (await db.execute(chat_statement)).scalar_one()
    except Exception as e:
        logger.error(f"Failed to retrieve chat {chat_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )

    if sender_id not in chat.user_ids:
        logger.error(f"User {sender_id} not authorized for chat {chat_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of this chat",
        )

    # Handle file attachment
    file_name = None
    if message_data is not None:
        try:
            # Read file data
            attachment_bytes = await message_data.read()
            if not attachment_bytes:
                logger.error("Empty file uploaded")
                raise HTTPException(status_code=400, detail="Empty file uploaded")

            # Generate unique filename
            file_extension = message_data.filename.split('.')[-1] if message_data.filename else 'bin'
            file_name = f"{uuid.uuid4().hex}_{int(datetime.now().timestamp())}.{file_extension}"
            
            logger.info(f"Saving attachment: {file_name}, size: {len(attachment_bytes)} bytes")

            # Save attachment to S3
            save_attachment(attachment_bytes, file_name, s3_client, cipher)

        except Exception as e:
            logger.error(f"Failed to process attachment: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process attachment: {str(e)}",
            )

    # Create and save the message
    try:
        message = Message(
            message_id=chat.current_message_id + 1,
            chat_id=chat_id,
            sender_id=sender_id,
            content=content,
            message_type=message_type,
            message_data=file_name,
            receive_remaining=[user_id for user_id in chat.user_ids if user_id != sender_id]
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
        logger.info(f"Message {message.message_id} saved successfully")

    except Exception as e:
        logger.error(f"Failed to save message to database: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save message",
        )

    # Prepare message data for broadcasting
    try:
        created_at_str = message.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        message_data = {
            "id": message.message_id,
            "chat_id": message.chat_id,
            "sender_id": message.sender_id,
            "content": message.content,
            "created_at": created_at_str,
            "message_type": message.message_type,
        }

        # Add file name if attachment exists
        if file_name:
            message_data["message_data"] = file_name

        logger.info(f"Broadcasting message to chat {chat_id}")
        if private:
            for friend in chat.friends:
                if friend.user_id != sender_id:
                    friend_room = get_user_room(friend.user_id)
                    await sio.emit(
                        "message_received",
                        message_data,
                        room=friend_room,
                    )
                    logger.debug(f"Message sent to user {friend.user_id}")
        else:
            group_room = get_group_room(chat_id)
            await sio.emit(
                "message_received",
                message_data,
                room=group_room,
            )
            logger.debug(f"Message sent to group {chat_id}")

    except Exception as e:
        logger.error(f"Failed to broadcast message: {str(e)}")
        # Don't fail the entire request if broadcasting fails

    return {"success": True, "data": message.message_id}
