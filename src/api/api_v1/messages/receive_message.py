from typing import List, Tuple

from fastapi import Depends, HTTPException, Security, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Select
from sqlmodel import select

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models import Friend, Group, Message, User, UserToken
from src.util.decorators import handle_db_errors
from src.util.security import checked_auth_token


class ReceievedMessageRequest(BaseModel):
    chat_id: int
    message_id: int


@api_router_v1.post("/message/received/single", status_code=200)
@handle_db_errors("receive messages failed")
async def message_received_single(
    receieved_message_request: ReceievedMessageRequest,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> dict:
    user, _ = user_and_token

    if user.id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User ID not found"
        )

    chat_id = receieved_message_request.chat_id
    message_id = receieved_message_request.message_id

    print(
        f"Processing single message received for chat_id: {chat_id}, message_id: {message_id}"
    )

    select_message_statement = (
        select(Message)
        .where(
            Message.message_id == message_id,
            Message.chat_id == chat_id,
        )
        .with_for_update(of=Message)
    )
    results_message = await db.execute(select_message_statement)
    message: Message = results_message.scalar_one()

    print(f"Message found: {message}")

    message.received_message(user.id)
    db.add(message)
    if message.received_by_all():
        print("Message received by all, setting for deletion")
        message.set_for_deletion()
        db.add(message)
    await db.commit()

    return {"success": True}


class ReceievedMessagesRequest(BaseModel):
    chat_id: int
    message_ids: List[int]


@api_router_v1.post("/message/received", status_code=200)
@handle_db_errors("receive messages failed")
async def message_received(
    receieved_messages_request: ReceievedMessagesRequest,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> dict:
    user, _ = user_and_token

    if user.id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User ID not found"
        )

    chat_id = receieved_messages_request.chat_id
    message_ids = receieved_messages_request.message_ids

    print(
        f"Processing multiple messages received for chat_id: {chat_id}, message_ids: {message_ids}"
    )

    select_messages_statement = (
        select(Message)
        .where(Message.message_id.in_(message_ids))
        .where(Message.chat_id == chat_id)
    )
    results_messages = await db.execute(select_messages_statement)
    result_messages: List[Message] = results_messages.scalars().all()

    print(f"Found {len(result_messages)} messages")

    for message in result_messages:
        print(f"Processing message: {message}")
        message.received_message(user.id)
        if message.received_by_all():
            print("Message received by all, setting for deletion")
            message.set_for_deletion()
            db.add(message)

    await db.commit()

    return {
        "success": True,
    }
