"""Endpoint for updating group details."""

from typing import Dict, Tuple

from fastapi import Depends, Security
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models.user import User
from src.models.user_token import UserToken
from src.util.decorators import handle_db_errors
from src.util.security import checked_auth_token
from src.util.util import get_group_room, get_chat_and_verify_admin
from src.util.rest_util import emit_group_response


class UpdateGroupRequest(BaseModel):
    """Request model for updating group details."""

    chat_id: int
    name: str | None = None
    description: str | None = None
    colour: str | None = None


@api_router_v1.post("/group/update", status_code=200)
@handle_db_errors("Group update failed")
async def update_group(
    update_group_request: UpdateGroupRequest,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, bool]:
    """Handle update group request."""
    me, _ = user_and_token

    chat_id = update_group_request.chat_id

    # Get chat and verify admin permissions
    chat = await get_chat_and_verify_admin(
        db,
        chat_id,
        me.id,  # type: ignore[arg-type]
        permission_error_detail="Only group admins can update group details",
    )

    # Update group details if provided
    if update_group_request.name is not None:
        chat.name = update_group_request.name
    if update_group_request.description is not None:
        chat.description = update_group_request.description
    if update_group_request.colour is not None:
        chat.colour = update_group_request.colour
    db.add(chat)

    for group in chat.groups:
        group.group_version += 1
        db.add(group)

    await db.commit()

    # TODO: Only send what is changed?
    group_room: str = get_group_room(chat_id)
    await emit_group_response("group_updated", chat, group_room)

    return {
        "success": True,
    }
