"""Endpoint for changing avatar of a group."""

from typing import Dict, Optional, Tuple

from fastapi import Depends, Form, HTTPException, Request, Security, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy.orm import selectinload

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models import Chat, User, UserToken
from src.sockets.sockets import sio
from src.util.decorators import handle_db_errors
from src.util.security import checked_auth_token
from src.util.util import get_group_room

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2MB


@api_router_v1.patch("/group/avatar", status_code=200, response_model=dict)
@handle_db_errors("Changing group avatar failed")
async def change_group_avatar(
    request: Request,
    group_id: int = Form(...),  # Must match the field name in FormData
    avatar: Optional[UploadFile] = None,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, bool]:
    """Handle change avatar request."""
    me, _ = user_and_token

    if me.id is None:
        raise HTTPException(status_code=400, detail="Can't find user")

    s3_client = request.app.state.s3
    cipher = request.app.state.cipher

    # TODO: Change other queries to use scalar_one where we expect one to exist?
    chat_statement = (
        select(Chat).where(Chat.id == group_id).options(selectinload(Chat.groups))
    )
    chat: Chat = (await db.execute(chat_statement)).scalar_one()

    if not avatar:
        chat.remove_group_avatar(s3_client)
        chat.default_avatar = True
        chat.avatar_version += 1
        for group in chat.groups:
            group.group_version += 1
            db.add(group)
        db.add(chat)
        await db.commit()

        group_room = get_group_room(group_id)
        await sio.emit(
            "group_avatar_updated",
            {"group_id": group_id, "avatar_version": chat.avatar_version},
            room=group_room,
        )

        return {"success": True}

    if not avatar.size or not avatar.filename:
        raise HTTPException(status_code=400, detail="Invalid avatar file")
    if avatar.size > MAX_AVATAR_SIZE:
        raise HTTPException(status_code=400, detail="Avatar too large (max 2MB)")
    if avatar.filename.split(".")[-1].lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PNG/JPG allowed")

    avatar_bytes = await avatar.read()
    chat.create_group_avatar(s3_client, cipher, avatar_bytes)
    chat.avatar_version += 1

    for group in chat.groups:
        group.group_version += 1
        db.add(group)

    if chat.default_avatar:
        chat.default_avatar = False
    db.add(chat)

    await db.commit()

    group_room = get_group_room(group_id)
    await sio.emit(
        "group_avatar_updated",
        {"group_id": group_id, "avatar_version": chat.avatar_version},
        room=group_room,
    )

    return {
        "success": True,
    }
