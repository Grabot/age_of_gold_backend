"""Endpoint for fetching all friends."""

from typing import Any, Dict, Tuple

from fastapi import Depends, Security
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models.friend import Friend
from src.models.user import User
from src.models.user_token import UserToken
from src.util.security import checked_auth_token


@api_router_v1.get("/friend/all", status_code=200)
async def fetch_all_friends(
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Handle fetch all friends request."""
    user, _ = user_and_token

    # Get all friends for the user (without JOIN, just Friend objects)
    friends_statement = select(Friend).where(Friend.user_id == user.id)
    friends_result = await db.execute(friends_statement)
    friends = friends_result.all()

    # Serialize friends data without user details (frontend will handle caching)
    friends_data = []
    for friend_row in friends:
        friend: Friend = friend_row.Friend
        friends_data.append(
            {
                "id": friend.id,
                "user_id": friend.user_id,
                "friend_id": friend.friend_id,
                "accepted": friend.accepted,
                "requested": not friend.accepted,  # If not accepted, it's requested
            }
        )

    return {"success": True, "data": friends_data}
