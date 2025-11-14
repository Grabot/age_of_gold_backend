from typing import Annotated
from urllib.parse import urlencode
from fastapi.responses import RedirectResponse
from fastapi import status
from src.api.api_v1.oauth.login_oauth import login_user_oauth
from src.api.api_v1.router import api_router_v1
from fastapi import Depends, Form, HTTPException, Request
from src.config.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.sockets.sockets import redis
import requests
import secrets
import jwt as pyjwt
import time


@api_router_v1.get("/auth/apple")
async def apple_login(request: Request):
    """Start Apple OAuth2 login"""
    auth_url = settings.APPLE_AUTHORIZE
    state = secrets.token_urlsafe(16)
    await redis.setex(f"oauth_state:{state}", settings.OAUTH_LIFETIME, "valid")
    params = {
        "response_type": "code id_token",
        "client_id": settings.APPLE_CLIENT_ID,
        "redirect_uri": settings.APPLE_REDIRECT_URL,
        "state": state,
        "scope": "name email",
        "response_mode": "form_post",
    }
    url_params = urlencode(params)
    authorization_url = f"{auth_url}?{url_params}"
    return RedirectResponse(url=authorization_url)


def generate_token():
    private_key = settings.APPLE_AUTH_KEY
    team_id = settings.APPLE_TEAM_ID
    client_id = settings.APPLE_CLIENT_ID
    key_id = settings.APPLE_KEY_ID
    validity_minutes = 15
    timestamp_now = int(time.time())
    timestamp_exp = timestamp_now + (60 * validity_minutes)
    data = {
        "iss": team_id,
        "iat": timestamp_now,
        "exp": timestamp_exp,
        "aud": settings.APPLE_AUD_URL,
        "sub": client_id,
    }
    token = pyjwt.encode(
        payload=data,
        key=private_key.encode("utf-8"),
        algorithm="ES256",
        headers={"kid": key_id},
    )
    return token


def decode_apple_token(token):
    try:
        return pyjwt.decode(
            token, audience=settings.APPLE_CLIENT_ID, options={"verify_signature": False}
        )
    except pyjwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ID token")


@api_router_v1.post("/auth/callback/apple")
async def apple_callback(
    code: Annotated[str, Form()],
    state: Annotated[str, Form()], # TODO: Test if this works, maybe state is url param?
    db: AsyncSession = Depends(get_db),
):
    """Handle Apple OAuth2 callback"""
    if not await redis.exists(f"oauth_state:{state}"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state"
        )
    await redis.delete(f"oauth_state:{state}")
    apple_key_url = settings.APPLE_AUTHORIZE_TOKEN
    userinfo_response = requests.post(
        apple_key_url,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_id": settings.APPLE_CLIENT_ID,
            "client_secret": generate_token(),
            "code": code,
            "grant_type": settings.APPLE_GRANT_TYPE,
            "redirect_uri": settings.APPLE_REDIRECT_URL,
        },
    )

    if (
        not userinfo_response.json().get("access_token")
        or not userinfo_response.json().get("refresh_token")
        or not userinfo_response.json().get("id_token")
    ):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="There was an error creating the user",
        )

    id_token = userinfo_response.json()["id_token"]
    apple_token = decode_apple_token(id_token)
    email = apple_token["email"]
    username = apple_token["email"].split("@")[0]

    return login_user_oauth(username, email, 4, db)
