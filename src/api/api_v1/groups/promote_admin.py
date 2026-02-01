"""Endpoint for promoting/demoting a user to/from admin in a group."""

from typing import Dict, Tuple

from fastapi import Depends, HTTPException, Security, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models import User
from src.models.user_token import UserToken
from src.util.decorators import handle_db_errors
from src.util.security import checked_auth_token
from src.util.util import get_chat_and_verify_admin
from src.util.rest_util import update_group_versions_and_notify


class PromoteAdminRequest(BaseModel):
    """Request model for promoting/demoting a user to/from admin."""

    group_id: int
    user_id: int
    is_admin: bool


@api_router_v1.post("/group/admin/promote", status_code=200)
@handle_db_errors("Promoting admin failed")
async def promote_admin(
    promote_admin_request: PromoteAdminRequest,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, bool]:
    """Handle promote/demote admin request."""
    me, _ = user_and_token

    group_id = promote_admin_request.group_id
    target_user_id = promote_admin_request.user_id
    is_admin = promote_admin_request.is_admin

    # Check if the current user is an admin of the group
    chat = await get_chat_and_verify_admin(
        db,
        group_id,
        me.id,
        permission_error_detail="Only group admins can change admin status",
    )

    # Check if the target user is in the group
    if target_user_id not in chat.user_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not in the group",
        )

    # Update admin status
    if is_admin:
        # Promote to admin
        if target_user_id not in chat.user_admin_ids:
            chat.add_admin(target_user_id)
    else:
        # Demote from admin
        if target_user_id in chat.user_admin_ids:
            chat.remove_admin(target_user_id)

    db.add(chat)

    await update_group_versions_and_notify(
        chat,
        db,
        me,
        "group_admin_changed",
        {
            "group_id": group_id,
            "user_id": target_user_id,
            "is_admin": is_admin,
        },
    )

    return {
        "success": True,
    }
