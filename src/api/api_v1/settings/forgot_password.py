"""Endpoint for when you forgot your password."""

from typing import Dict

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Select
from sqlmodel import select

from age_of_gold_worker.age_of_gold_worker.tasks import task_send_email_forgot_password
from src.api.api_v1.router import api_router_v1
from src.database import get_db
from src.models.user import User, hash_email
from src.models.user_token import UserToken
from src.util.decorators import handle_db_errors
from src.util.util import get_user_tokens


class PasswordForgotRequest(BaseModel):
    """Request model for forgot password."""

    email: str


@api_router_v1.post("/password/forgot", status_code=200)
@handle_db_errors("Forgot password failed")
async def forgot_password(
    password_forgot_request: PasswordForgotRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, bool]:
    """Handle forgot password request."""
    email_to_send = password_forgot_request.email

    hashed_email = hash_email(email_to_send)
    statement: Select = (
        select(User).where(User.origin == 0).where(User.email_hash == hashed_email)
    )
    results = await db.execute(statement)
    result_user = results.first()
    if not result_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="no account found using this email",
        )

    user: User = result_user.User

    user_token: UserToken = get_user_tokens(user, 1800, 1800)
    db.add(user_token)
    await db.commit()

    subject = "Reset your password - Age of Gold"

    _ = task_send_email_forgot_password.delay(
        to_email=email_to_send,
        subject=subject,
        access_token=user_token.access_token,
    )

    return {
        "success": True,
    }
