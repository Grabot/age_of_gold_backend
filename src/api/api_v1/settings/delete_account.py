"""Endpoint for deleting account."""

from typing import Tuple

from fastapi import Depends, HTTPException, Security, status, Request
from pydantic import BaseModel
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.selectable import Select
from sqlmodel import select

from age_of_gold_worker.age_of_gold_worker.tasks import task_send_email_delete_account
from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models.user import User, hash_email
from src.models.user_token import UserToken
from src.util.decorators import handle_db_errors
from src.util.gold_logging import logger
from src.util.security import checked_auth_token
from src.util.util import get_user_tokens


@api_router_v1.delete("/delete/account", status_code=status.HTTP_200_OK)
@handle_db_errors("Delete account failed")
async def delete_account(
    request: Request,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    """Delete the user's account."""
    s3_client = request.app.state.s3
    me, _ = user_and_token
    logger.info("Deleting account for user: %s", me.username)
    await db.execute(delete(UserToken).where(UserToken.user_id == me.id))  # type: ignore
    me.remove_avatar(s3_client)
    me.remove_avatar_default(s3_client)
    await db.delete(me)
    await db.commit()
    return {"success": True}


class DeleteAccountRequest(BaseModel):
    """Request model for deleting accounts."""

    email: str


@api_router_v1.post("/delete/account/request", status_code=status.HTTP_200_OK)
@handle_db_errors("Delete account request failed")
async def delete_account_request_call(
    delete_account_request: DeleteAccountRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    """Request to delete an account by sending an email."""
    email_hash = hash_email(delete_account_request.email.strip())
    statement: Select = select(User).where(User.email_hash == email_hash)
    results = await db.execute(statement)
    result = results.all()
    if result is None or result == []:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email",
        )

    user: User = result[0].User
    user_token = get_user_tokens(user, 1800, 1800)
    db.add(user_token)
    await db.commit()

    subject = "Age of Gold - Delete your account"
    _ = task_send_email_delete_account.delay(
        delete_account_request.email.strip(), subject, user_token.access_token
    )

    return {"success": True}


@api_router_v1.delete("/delete/account/all", status_code=200)
@handle_db_errors("Delete accounts failed")
async def delete_account_all(
    request: Request,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    """Delete all accounts associated with the user's email."""
    me, _ = user_and_token

    origins_statement: Select = (
        select(User)
        .where(User.email_hash == me.email_hash)
        .options(selectinload(User.tokens))  # type: ignore
    )
    origins_results = await db.execute(origins_statement)
    origins_result = origins_results.all()

    s3_client = request.app.state.s3

    for origin_result in origins_result:
        user_delete: User = origin_result.User
        await db.execute(delete(UserToken).where(UserToken.user_id == user_delete.id))  # type: ignore
        user_delete.remove_avatar(s3_client)
        user_delete.remove_avatar_default(s3_client)
        await db.delete(user_delete)
    await db.commit()

    return {
        "success": True,
    }
