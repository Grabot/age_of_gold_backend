import time
from typing import Optional

from config import settings
from fastapi import Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from util.email.email import EmailProcess
from util.email.verification_email import verification_email
from util.util import check_token, decode_token, get_auth_token

from app.api.api_v1 import api_router_v1
from app.api.rest_util import get_failed_response
from app.database import get_db
from app.models import User


class VerifyEmailRequest(BaseModel):
    access_token: str
    new_password: str


@api_router_v1.post("/email/verification", status_code=200)
async def verify_email_post(
    verify_email_request: VerifyEmailRequest, response: Response, db: AsyncSession = Depends(get_db)
) -> dict:
    access_token = verify_email_request.access_token
    decoded_token = decode_token(access_token)

    if "id" not in decoded_token or "exp" not in decoded_token:
        return get_failed_response("invalid token", response)

    user_id = decoded_token["id"]
    expiration = decoded_token["exp"]

    if not user_id or not expiration:
        return get_failed_response("no user found", response)

    if expiration < int(time.time()):
        return get_failed_response("verification email expired", response)

    statement = select(User).filter_by(id=user_id)
    results = await db.execute(statement)
    result_user = results.first()
    if not result_user:
        return get_failed_response("no account found using this email", response)
    user = result_user.User

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
        get_failed_response("An error occurred", response)

    user_request: Optional[User] = await check_token(db, auth_token)
    if not user_request:
        get_failed_response("An error occurred", response)

    expiration_time = 18000  # 5 hours
    reset_token = user_request.generate_auth_token(expiration_time).decode("ascii")
    subject = "Age of Gold - Verify your email"
    body = verification_email.format(base_url=settings.BASE_URL, token=reset_token)
    p = EmailProcess(user_request.email, subject, body)
    p.start()

    return {
        "result": True,
        "message": "Email verification email send",
    }
