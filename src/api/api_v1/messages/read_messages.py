from typing import Tuple, List

from fastapi import Depends, HTTPException, Security, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models import User, UserToken, Chat, Group, Friend
from sqlalchemy.sql.selectable import Select
from sqlalchemy.orm import selectinload
from src.util.security import checked_auth_token
from src.util.util import get_group_room
from src.sockets.sockets import sio
from enum import IntEnum


class ChatType(IntEnum):
    GROUP = 0
    FRIEND = 1

class ReadMessageRequest(BaseModel):
    chat_id: int
    last_message_read_id: int
    type: ChatType


@api_router_v1.post("/message/read", status_code=200)
async def message_read(
    read_message_request: ReadMessageRequest,
    user_and_token: Tuple[User, UserToken] = Security(checked_auth_token, scopes=["user"]),
    db: AsyncSession = Depends(get_db),
) -> dict:
    user, _ = user_and_token
    chat_id = read_message_request.chat_id
    last_message_read_id = read_message_request.last_message_read_id

    if user.id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User ID not found")

    print(f"Processing message read for chat_id: {chat_id} (type: {read_message_request.type})")

    # Branch based on type
    if read_message_request.type == ChatType.GROUP:
        statement = select(Group).where(Group.chat_id == chat_id).with_for_update(of=Group)
        entities: List[Group] = (await db.execute(statement)).scalars().all()
    elif read_message_request.type == ChatType.FRIEND:
        statement = select(Friend).where(Friend.chat_id == chat_id).with_for_update(of=Friend)
        entities: List[Friend] = (await db.execute(statement)).scalars().all()
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid type")

    # Shared logic for updating entities
    lowest_last_message_read_id = last_message_read_id
    for entity in entities:
        if entity.last_message_read_id < lowest_last_message_read_id:
            lowest_last_message_read_id = entity.last_message_read_id
        if entity.user_id == user.id:
            entity.last_message_read_id = last_message_read_id
            entity.unread_messages = 0
            db.add(entity)
    await db.commit()

    # Fetch and update Chat (shared)
    chat_statement = (
        select(Chat)
        .where(Chat.id == chat_id)
        .with_for_update(of=Chat)
        .options(selectinload(Chat.groups))
    )
    chat: Chat = (await db.execute(chat_statement)).scalar_one()
    if chat.last_message_read_id_chat < lowest_last_message_read_id:
        chat.last_message_read_id_chat = lowest_last_message_read_id
        db.add(chat)
        for group in chat.groups:
            group.group_version += 1
            db.add(group)
        room = get_group_room(chat_id)
        socket_response = {
            "last_message_read_id": lowest_last_message_read_id,
            "chat_id": chat_id,
        }
        await sio.emit("message_read", socket_response, room=room)
        await db.commit()

    print(f"Message read processed successfully for chat_id: {chat_id}")
    return {"success": True}
