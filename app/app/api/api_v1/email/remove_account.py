import time
from typing import Optional
from fastapi import Request, Depends
from pydantic import BaseModel
from fastapi import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.api_v1 import api_router_v1
from app.celery_worker.tasks import task_send_email
from app.config.config import settings
from app.database import get_db
from app.models import User, UserToken
from app.util.email.delete_account_email import delete_account_email
from app.util.rest_util import get_failed_response
from app.util.util import refresh_user_token
from sqlalchemy.orm import selectinload
from app.util.util import check_token, get_auth_token
import hashlib


async def send_delete_email(user: User, email: str, origin: int):
    access_expiration_time = 1800  # 30 minutes
    refresh_expiration_time = 18000  # 5 hours
    token_expiration = int(time.time()) + access_expiration_time
    refresh_token_expiration = int(time.time()) + refresh_expiration_time
    delete_token = user.generate_auth_token(access_expiration_time).decode("ascii")
    refresh_delete_token = user.generate_refresh_token(refresh_expiration_time).decode("ascii")

    subject = "Hex Place - Delete your account"
    body = delete_account_email.format(
        base_url=settings.BASE_URL, token=delete_token, refresh_token=refresh_delete_token, origin=origin
    )
    _ = task_send_email.delay(user.username, email, subject, body)

    user_token = UserToken(
        user_id=user.id,
        access_token=delete_token,
        refresh_token=refresh_delete_token,
        token_expiration=token_expiration,
        refresh_token_expiration=refresh_token_expiration,
    )
    return user_token


class RemoveAccountRequest(BaseModel):
    email: str


@api_router_v1.post("/remove/account", status_code=200)
async def remove_account(
    remove_account_request: RemoveAccountRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:

    email = remove_account_request.email
    email_hash = hashlib.sha512(email.lower().encode("utf-8")).hexdigest()
    statement = (
        select(User)
        .where(User.email_hash == email_hash)
        .options(selectinload(User.friends))
        .options(selectinload(User.tokens))
    )
    results = await db.execute(statement)
    result = results.all()
    if result is None or result == []:
        return get_failed_response(
            "no account found with that email", response
        )

    user = result[0].User
    # origin 9 means all the accounts with the email will be deleted
    user_token = await send_delete_email(user, email, 9)
    db.add(user_token)
    await db.commit()

    return {
        "result": True,
        "message": "Account deletion email has been sent",
    }


@api_router_v1.post("/remove/account/token", status_code=200)
async def remove_account_token(
    remove_account_request: RemoveAccountRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:

    email = remove_account_request.email
    auth_token = get_auth_token(request.headers.get("Authorization"))

    if auth_token == "":
        return get_failed_response("An error occurred", response)

    user: Optional[User] = await check_token(db, auth_token)
    if not user:
        return get_failed_response("An error occurred", response)

    email_hash = hashlib.sha512(email.lower().encode("utf-8")).hexdigest()
    if email_hash == user.email_hash:
        user_token = await send_delete_email(user, email, user.origin)
        db.add(user_token)
        await db.commit()
        return {
            "result": True,
            "message": "Account deletion email has been sent",
        }
    else:
        return {
            "result": False,
            "message": "Email is not the same as the account email",
        }


class RemoveAccountVerifyRequest(BaseModel):
    access_token: str
    refresh_token: str
    origin: int


@api_router_v1.post("/remove/account/verify", status_code=200)
async def remove_account_verify(
    remove_account_verify_request: RemoveAccountVerifyRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:

    access_token = remove_account_verify_request.access_token
    refresh_token = remove_account_verify_request.refresh_token
    origin = remove_account_verify_request.origin
    user: Optional[User] = await refresh_user_token(db, access_token, refresh_token)

    if not user:
        return get_failed_response("user not found", response)

    if origin != 9:
        user_tokens = user.tokens
        for user_token in user_tokens:
            await db.delete(user_token)
        await db.commit()

        await db.delete(user)
        await db.commit()
        return {
            "result": True,
            "message": "Account deletion has been cancelled",
        }
    else:
        hashed_email = user.email_hash
        # Get all the accounts with the same email by checking the hash in the db
        statement = (
            select(User)
            .where(User.email_hash == hashed_email)
            .options(selectinload(User.tokens))
        )
        results = await db.execute(statement)
        users = results.all()
        if users is None or users == []:
            return get_failed_response(
                "no account found with that email", response
            )

        # First delete tokens, otherwise we can't delete the user
        for user in users:
            log_user = user.User
            user_tokens = log_user.tokens
            for user_token in user_tokens:
                await db.delete(user_token)
        await db.commit()

        # Then delete the user, which might be multiple because of oauth2
        for user in users:
            await db.delete(user.User)
        await db.commit()

        return {
            "result": True,
            "message": "Account has been removed",
        }
