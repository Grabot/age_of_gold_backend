import requests
from app.api.api_v1 import api_router_v1
from app.celery_worker.tasks import task_generate_avatar
from app.config.config import settings
from app.database import get_db
from app.api.api_login.logins.login_user_origin import login_user_origin
from app.util.rest_util import get_failed_response
from app.util.util import get_user_tokens
from fastapi import Depends, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession



async def log_user_in(
        userinfo_response,
        db: AsyncSession = Depends(get_db),
):
    users_email = userinfo_response.json()["email"]
    users_name = userinfo_response.json()["given_name"]

    [user, user_created] = await login_user_origin(users_name, users_email, 1, db)

    if user:
        user_token = get_user_tokens(user, 30, 60)
        db.add(user_token)
        await db.commit()
        access_token = user_token.access_token
        refresh_token = user_token.refresh_token

        if user_created:
            db.add(user)
            await db.refresh(user)
            await db.commit()
            _ = task_generate_avatar.delay(user.avatar_filename(), user.id)
        else:
            await db.commit()

        return [True, [access_token, refresh_token, user, user_created]]
    else:
        return [False, [None, None, None, None]]


class GoogleTokenRequest(BaseModel):
    access_token: str


# User the v1 router, so it will have `api/v1.0/` before the path
@api_router_v1.post("/login/google/token", status_code=200)
async def login_google_token(
        google_token_request: GoogleTokenRequest,
        response: Response,
        db: AsyncSession = Depends(get_db),
) -> dict:

    google_access_token = google_token_request.access_token
    userinfo_response = requests.get(
        f"{settings.GOOGLE_ACCESS_TOKEN_URL}?access_token={google_access_token}",
    )

    if userinfo_response.json().get("error", None):
        return get_failed_response("An error occurred", response)

    # You want to make sure their email is verified.
    # The user authenticated with Google, authorized your
    # app, and now you've verified their email through Google!
    if not userinfo_response.json().get("email_verified"):
        return get_failed_response("User email not available or not verified by Google.", response)

    # We don't use the tokens send with this,
    # because they are only valid for a short period, and we will refresh them later on
    [success, [_, _, user, user_created]] = await log_user_in(userinfo_response, db)

    if success:

        # Valid login, we refresh the token for this user.
        user_token = get_user_tokens(user)
        db.add(user_token)
        await db.commit()

        if user_created:
            user = user.serialize_no_detail
        else:
            user = user.serialize

        # We don't refresh the user object because we know all we want to know
        login_response = {
            "result": True,
            "message": "user logged in successfully.",
            "access_token": user_token.access_token,
            "refresh_token": user_token.refresh_token,
            "user": user,
        }

        return login_response
    else:
        return get_failed_response("An error occurred", response)


