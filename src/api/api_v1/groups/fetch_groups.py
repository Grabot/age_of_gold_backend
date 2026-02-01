"""Endpoint for fetching all groups."""

from typing import Any, Dict, List, Optional, Tuple

from fastapi import Depends, Security
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models.group import Group
from src.models.user import User
from src.models.user_token import UserToken
from src.util.decorators import handle_db_errors
from src.util.security import checked_auth_token


class FetchGroupsRequest(BaseModel):
    """Request model for fetching groups with optional group ID filter."""

    group_ids: Optional[List[int]] = None


@api_router_v1.post("/group/all", status_code=200)
@handle_db_errors("Fetching groups failed")
async def fetch_all_groups(
    fetch_groups_request: FetchGroupsRequest,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Handle fetch all groups request."""
    user, _ = user_and_token

    # Get all groups for the user
    groups_statement = select(Group).where(Group.user_id == user.id)

    # If group_ids filter is provided, add it to the query
    if fetch_groups_request.group_ids is not None:
        groups_statement = groups_statement.where(
            Group.group_id.in_(fetch_groups_request.group_ids)  # pylint: disable=no-member
        ).options(selectinload(Group.chat))
    else:
        groups_statement = groups_statement.options(selectinload(Group.chat))

    groups_result = await db.execute(groups_statement)
    groups = groups_result.scalars().all()  # Directly get a list of Group objects

    # Serialize groups data without chat details
    groups_data = [group.serialize for group in groups]

    return {"success": True, "data": groups_data}
