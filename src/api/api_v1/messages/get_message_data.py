from io import BytesIO
from typing import Optional, Tuple
from fastapi import Depends, Request, Response, Security, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.api.api_v1.router import api_router_v1
from src.util.decorators import handle_db_errors
from src.database import get_db
from src.models.chat import Chat
from src.models.message import Message
from src.models.user import User
from src.models.user_token import UserToken
from src.sockets.sockets import sio
from src.util.security import checked_auth_token


class GetMessageDataRequest(BaseModel):
    chat_id: int
    message_id: int


@api_router_v1.post("/message/data", status_code=200)
@handle_db_errors("Get message data failed")
async def get_messages_data(
    get_message_data_request: GetMessageDataRequest,
    request: Request,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Handle get message data request."""
    me, _ = user_and_token

    print(f"Received request for message data: chat_id={get_message_data_request.chat_id}, message_id={get_message_data_request.message_id}")
    
    s3_client = request.app.state.s3
    cipher = request.app.state.cipher

    if me.id is None:
        print("User ID not found")
        raise HTTPException(status_code=400, detail="User ID not found")

    chat_id = get_message_data_request.chat_id
    message_id = get_message_data_request.message_id

    print(f"Querying database for message with chat_id={chat_id}, message_id={message_id}")
    
    select_statement = (
        select(Message)
        .where(
            Message.chat_id == chat_id,
            Message.message_id == message_id,
        )
        .order_by(Message.message_id)
    )
    message_with_data: Message = (await db.execute(select_statement)).scalar_one_or_none()
    if message_with_data is None:
        print("Message not found in database")
        return Response(
            content="Message can not be found",
            media_type="text/plain",
            status_code=500
        )

    print(f"Retrieving message data for message_id={message_id}")
    
    s3_client = request.app.state.s3
    cipher = request.app.state.cipher

    data_bytes = message_with_data.get_message_data(s3_client, cipher)
    if data_bytes is None:
        print("Failed to retrieve message data")
        return Response(
            content="Message data could not be retrieved",
            media_type="text/plain",
            status_code=500
        )

    print(f"Marking message_id={message_id} as received by user_id={me.id}")
    
    message_with_data.received_message(me.id)
    if message_with_data.received_by_all():
        print("Message received by all, setting for deletion")
        message_with_data.set_for_deletion()
        db.add(message_with_data)

    await db.commit()

    print(f"Successfully retrieved message data for message_id={message_id}")
    
    decrypted_buffer: BytesIO = BytesIO(data_bytes)
    decrypted_buffer.seek(0)
    return StreamingResponse(
        decrypted_buffer,
        media_type="image/png",
        headers={"Content-Disposition": f"inline; filename={message_with_data.message_data}"},
    )
