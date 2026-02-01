"""Endpoint for fetching all friends."""

from typing import Any, Dict, List, Optional, Tuple

from fastapi import Depends, Security
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Select
from sqlmodel import select

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models.friend import Friend
from src.models.user import User
from src.models.user_token import UserToken
from src.util.decorators import handle_db_errors
from src.util.security import checked_auth_token


class FetchFriendsRequest(BaseModel):
    """Request model for fetching friends with optional user ID filter."""

    user_ids: Optional[List[int]] = None


@api_router_v1.post("/friend/all", status_code=200)
@handle_db_errors("Fetching friends failed")
async def fetch_all_friends(
    fetch_friends_request: FetchFriendsRequest,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Handle fetch all friends request."""
    user, _ = user_and_token

    friends_statement: Select = select(Friend).where(Friend.user_id == user.id)

    # If user_ids filter is provided, add it to the query
    if fetch_friends_request.user_ids is not None:
        friends_statement = friends_statement.where(
            Friend.friend_id.in_(fetch_friends_request.user_ids)  # pylint: disable=no-member
        )

    friends_result = await db.execute(friends_statement)
    friends = friends_result.scalars().all()

    # Serialize friends data without user details (frontend will handle caching)
    friends_data = [
        {
            "id": friend.id,
            "friend_id": friend.friend_id,
            "accepted": friend.accepted,
            "friend_version": friend.friend_version,
        }
        for friend in friends
    ]

    return {"success": True, "data": friends_data}
