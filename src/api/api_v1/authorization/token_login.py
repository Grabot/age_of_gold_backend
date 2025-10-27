"""Endpoint for token-based login."""

from typing import Any, Tuple

from fastapi import Depends, Response, Security
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models.user import User
from src.models.user_token import UserToken
from src.util.decorators import handle_db_errors
from src.util.security import checked_auth_token
from src.util.util import get_user_tokens


@api_router_v1.post("/login/token", status_code=200)
@handle_db_errors("Token login failed")
async def login_token_user(
    response: Response,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Handle token-based login request."""
    user, user_token_old = user_and_token
    user_token_new = get_user_tokens(user)
    await db.delete(user_token_old)
    db.add(user_token_new)
    await db.commit()

    login_response = {
        "result": True,
        "access_token": user_token_new.access_token,
        "refresh_token": user_token_new.refresh_token,
    }
    return login_response
