import time

from fastapi import Depends, Response
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.api_v1 import api_router_v1
from app.api.rest_util import get_failed_response
from app.celery_worker.tasks import task_send_email
from app.config.config import settings
from app.database import get_db
from app.models import User
from app.util.email.reset_password_email import reset_password_email


class PasswordResetRequest(BaseModel):
    email: str


@api_router_v1.post("/password/reset", status_code=200)
async def reset_password(
    password_reset_request: PasswordResetRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    email = password_reset_request.email

    statement = select(User).where(User.origin == 0).where(func.lower(User.email) == email.lower())
    results = await db.execute(statement)
    result_user = results.first()
    if not result_user:
        return get_failed_response("no account found using this email", response)

    user: User = result_user.User
    expiration_time = 18000  # 5 hours
    token_expiration = int(time.time()) + expiration_time
    reset_token = user.generate_auth_token(expiration_time).decode("ascii")

    print("attempting to send an email to %s" % email)
    subject = "Age of Gold - Change your password"
    body = reset_password_email.format(base_url=settings.BASE_URL, token=reset_token)

    task = task_send_email.delay(user.username, user.email, subject, body)
    print(f"send forgotten password email! {task}")

    user.set_token(reset_token)
    user.set_token_expiration(token_expiration)
    db.add(user)
    await db.commit()
    return {
        "result": True,
        "message": "password check was good",
    }
