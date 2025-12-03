import time
from typing import Any, Optional, Tuple

import jwt as pyjwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.selectable import Select
from sqlmodel import select

from src.config.config import settings
from src.database import get_db
from src.models.user import User
from src.models.user_token import UserToken

security = HTTPBearer()


async def get_valid_auth_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> str:
    """Validates the authorization token from the request"""
    auth_token = credentials.credentials
    if not auth_token.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization token is missing or invalid",
        )
    return auth_token


def decode_token(token: str, token_type: str) -> bool:
    """Decodes and verifies the JWT token"""
    try:
        payload: dict[str, Any] = pyjwt.decode(
            token,
            settings.jwt_pem,
            algorithms=[settings.header["alg"]],
            audience=settings.JWT_AUD,
            issuer=settings.JWT_ISS,
        )
        if payload.get("typ") != token_type:
            return False
        return True
    except pyjwt.PyJWTError:
        return False


async def check_token(
    db: AsyncSession, token: str, token_type: str
) -> Tuple[Optional[User], Optional[UserToken]]:
    """Checks the validity of the token and retrieves the associated user and token"""
    if not decode_token(token, token_type):
        return None, None
    token_statement: Select
    if token_type == "access":
        token_statement = (
            select(UserToken)
            .options(joinedload(UserToken.user))  # type: ignore[attr-defined]
            .filter_by(access_token=token)
        )
    else:
        token_statement = (
            select(UserToken)
            .options(joinedload(UserToken.user))  # type: ignore[attr-defined]
            .filter_by(refresh_token=token)
        )
    results_token = await db.execute(token_statement)
    result_token = results_token.first()
    if result_token is None:
        return None, None
    user_token: UserToken = result_token.UserToken
    if user_token.token_expiration < int(time.time()):
        return None, None

    user: User = user_token.user
    return user, user_token


async def checked_auth_token(
    auth_token: str = Security(get_valid_auth_token, scopes=["user"]),
    db: AsyncSession = Depends(get_db),
) -> Tuple[User, UserToken]:
    """Checks the authorization token and retrieves the associated user and token"""
    user, token = await check_token(db, auth_token, "access")

    if not user or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token is invalid or expired",
        )
    return user, token
