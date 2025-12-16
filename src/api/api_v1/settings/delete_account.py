from typing import Tuple
from fastapi import Depends, Security, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

from src.api.api_v1.router import api_router_v1
from src.models.user import User
from src.models.user_token import UserToken
from src.util.decorators import handle_db_errors
from src.database import get_db
from src.util.gold_logging import logger
from src.util.security import checked_auth_token


@api_router_v1.delete("/delete/account", status_code=status.HTTP_200_OK)
@handle_db_errors("Delete account failed")
async def delete_account(
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> dict:    
    me, _ = user_and_token
    logger.info("Deleting account for user: %s", me.username)
    await db.execute(
        delete(UserToken)
        .where(UserToken.user_id == me.id)
    )
    await db.delete(me)
    await db.commit()
    return {
        "success": True
    }
