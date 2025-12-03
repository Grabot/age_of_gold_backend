"""Endpoint for token-based login."""

from typing import Tuple

from fastapi import Depends, Security
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models.user import User
from src.models.user_token import UserToken
from src.util.decorators import handle_db_errors
from src.util.security import checked_auth_token
from src.util.util import (
    SuccessfulLoginResponse,
    get_successful_login_response,
    get_user_tokens,
)


@api_router_v1.post("/login/token", status_code=200)
@handle_db_errors("Token login failed")
async def login_token_user(
    user_and_token: Tuple[User, UserToken] = Security(checked_auth_token),
    db: AsyncSession = Depends(get_db),
) -> SuccessfulLoginResponse:
    """Handle token-based login request."""
    user, old_token = user_and_token
    new_token = get_user_tokens(user)

    old_token.access_token = new_token.access_token
    old_token.refresh_token = new_token.refresh_token
    old_token.token_expiration = new_token.token_expiration
    old_token.refresh_token_expiration = new_token.refresh_token_expiration
    db.add(old_token)
    await db.commit()

    return get_successful_login_response(old_token, user)
