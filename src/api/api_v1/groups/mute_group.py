"""Endpoint for muting/unmuting a group."""

from typing import Dict, Tuple
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, Security, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models.group import Group
from src.models.user import User
from src.models.user_token import UserToken
from src.util.security import checked_auth_token


class MuteGroupRequest(BaseModel):
    """Request model for muting/unmuting a group."""

    group_id: int
    mute: bool
    mute_duration_hours: int | None = None


@api_router_v1.post("/group/mute", status_code=200)
async def mute_group(
    mute_group_request: MuteGroupRequest,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, bool]:
    """Handle mute/unmute group request."""
    me, _ = user_and_token

    if me.id is None:
        raise HTTPException(status_code=400, detail="Can't find user")

    group_id = mute_group_request.group_id
    mute = mute_group_request.mute
    mute_duration_hours = mute_group_request.mute_duration_hours

    # Get the group entry for this user
    group_statement = select(Group).where(
        Group.user_id == me.id, Group.group_id == group_id
    )
    group_result = await db.execute(group_statement)
    group_entry = group_result.first()

    if not group_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    group: Group = group_entry.Group

    # Update mute status
    group.mute = mute

    if mute and mute_duration_hours:
        # Set mute timestamp if muting with duration
        group.mute_timestamp = datetime.utcnow() + timedelta(hours=mute_duration_hours)
    else:
        # Clear mute timestamp if unmuting or muting indefinitely
        group.mute_timestamp = None

    await db.commit()

    return {
        "success": True,
    }
