import time
from typing import Optional

from fastapi import Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.api_v1 import api_router_v1
from app.api.rest_util import get_failed_response
from app.celery_worker.tasks import task_send_email
from app.config.config import settings
from app.database import get_db
from app.models import User, UserToken
from app.util.email.verification_email import verification_email
from app.util.util import check_token, get_auth_token, refresh_user_token


class VerifyEmailRequest(BaseModel):
    access_token: str
    refresh_token: str


@api_router_v1.post("/email/verification", status_code=200)
async def verify_email_post(
    verify_email_request: VerifyEmailRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    access_token = verify_email_request.access_token
    refresh_token = verify_email_request.refresh_token

    user: Optional[User] = await refresh_user_token(db, access_token, refresh_token)
    if not user:
        return get_failed_response("user not found", response)

    if user.is_verified():
        return {
            "result": True,
            "message": "Email %s has already been verified!" % user.email,
        }

    else:
        user.verify_user()
        db.add(user)
        await db.commit()

        return {
            "result": True,
            "message": "Email %s is verified!" % user.email,
        }


@api_router_v1.get("/email/verification", status_code=200)
async def verify_email_get(
    request: Request, response: Response, db: AsyncSession = Depends(get_db)
) -> dict:
    auth_token = get_auth_token(request.headers.get("Authorization"))
    if auth_token == "":
        return get_failed_response("An error occurred", response)

    user_request: Optional[User] = await check_token(db, auth_token)
    if not user_request:
        return get_failed_response("An error occurred", response)

    access_expiration_time = 1800  # 30 minutes
    refresh_expiration_time = 18000  # 5 hours
    token_expiration = int(time.time()) + access_expiration_time
    refresh_token_expiration = int(time.time()) + refresh_expiration_time
    reset_token = user_request.generate_auth_token(access_expiration_time).decode("ascii")
    refresh_reset_token = user_request.generate_auth_token(refresh_expiration_time).decode("ascii")
    subject = "Age of Gold - Verify your email"
    body = verification_email.format(
        base_url=settings.BASE_URL, token=reset_token, refresh_token=refresh_reset_token
    )

    task = task_send_email.delay(user_request.username, user_request.email, subject, body)
    print(f"send verify email email! {task}")

    user_token = UserToken(
        user_id=user_request.id,
        access_token=reset_token,
        refresh_token=refresh_reset_token,
        token_expiration=token_expiration,
        refresh_token_expiration=refresh_token_expiration,
    )
    db.add(user_token)
    await db.commit()

    return {
        "result": True,
        "message": "Email verification email send",
    }
