import re
from fastapi.responses import RedirectResponse
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

import hashlib

from src.celery_worker.tasks import task_generate_avatar
from src.config.config import settings
from src.models.user import User
from src.util.util import get_user_tokens


# TODO: Why also a boolean? Make it more clear and readable?
async def login_user_oauth(
    username: str,
    email: str,
    origin: int,
    db: AsyncSession,
):
    # Some very simple pre-check to make sure the username will not be email formatted.
    if re.match(
        r"^[a-zA-Z0-9.a-zA-Z0-9.!#$%&'*+-/=?^_`{|}~]+@[a-zA-Z0-9]+\.[a-zA-Z]+",
        username,
    ):
        username = username.replace("@", "")

    # Check if the user has logged in before using this origin.
    # If that's the case it has a Row in the User database, and we log in
    hashed_email = hashlib.sha512(email.lower().encode("utf-8")).hexdigest()
    statement_origin = (
        select(User).where(User.origin == origin).where(User.email_hash == hashed_email)
    )
    results_origin = await db.execute(statement_origin)
    result_user_origin = results_origin.first()
    user_created = False
    if result_user_origin:
        user: User = result_user_origin.User
        user_created = False
    else:
        # If not than we create a new entry in the User table and then log in.
        # The last verification is to check if username is not taken
        statement_name = select(User).where(
            func.lower(User.username) == username.lower()
        )
        results_username = await db.execute(statement_name)
        result_username = results_username.first()
        if not result_username:
            user = User(
                username=username,
                email_hash=hashed_email,
                password_hash="",
                salt="",
                origin=origin,
            )
            db.add(user)
            await db.commit()
            user_created = True
        else:
            # If the username is taken than we change it
            # because we have to create the user here.
            # The user can change it later if that person really hates the name that is given.
            new_user_name = username
            index = 2
            while index < 1000:
                statement_name_new = select(User).where(
                    func.lower(User.username) == new_user_name.lower(),
                )
                results_name_new = await db.execute(statement_name_new)
                result_username_new = results_name_new.first()

                if not result_username_new:
                    user = User(
                        username=new_user_name,
                        email_hash=hashed_email,
                        password_hash="",
                        salt="",
                        origin=origin,
                    )
                    db.add(user)
                    await db.commit()
                    return (user, True)
                else:
                    new_user_name = f"{username}_{index}"
                    index += 1
                    
            return HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Couldn't create the user",
            )

    if user:
        if user_created:
            await db.refresh(user)
            _ = task_generate_avatar.delay(user.avatar_filename(), user.id)
        user_token = get_user_tokens(user, 60, 120)
        db.add(user_token)
        await db.commit()
        access_token = user_token.access_token
    else:
        # TODO: Httpexception?
        raise Exception("User creation failed")

    redirect_url = f"{settings.FRONTEND_URL}/auth/callback?token={access_token}"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
