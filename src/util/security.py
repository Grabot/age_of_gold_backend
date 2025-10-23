from typing import Optional, Tuple
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import HTTPException, Security, status
import time
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.selectable import Select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from fastapi import Depends
from sqlmodel import select

from src.models.user import User
from src.models.user_token import UserToken

security = HTTPBearer()


async def get_valid_auth_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> str:
    auth_token = credentials.credentials
    if not auth_token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token is missing or invalid",
        )
    return auth_token


async def check_token(
    db: AsyncSession, token: str
) -> Tuple[Optional[User], Optional[UserToken]]:
    token_statement: Select = (
        select(UserToken)
        .options(joinedload(UserToken.user))
        .filter_by(access_token=token)
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
) -> Tuple[Optional[User], Optional[UserToken]]:
    user, token = await check_token(db, auth_token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token is invalid or expired",
        )
    return user, token
