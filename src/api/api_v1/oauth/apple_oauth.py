"""Handler for the Apple oauth2 flow"""

import secrets
import time
from typing import Annotated, Any
from urllib.parse import urlencode

import httpx
import jwt as pyjwt
from fastapi import Depends, Form, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.oauth.login_oauth import (
    login_user_oauth,
    redirect_oauth,
    validate_oauth_state,
)
from src.api.api_v1.router import api_router_v1
from src.config.config import settings
from src.database import get_db
from src.models.user import User
from src.sockets.sockets import redis
from src.util.util import (
    SuccessfulLoginResponse,
    get_successful_login_response,
    get_user_tokens,
)


async def validate_apple_user(apple_access_token: str, db: AsyncSession) -> User:
    """Validates an Apple user using the provided access token."""
    apple_token = decode_apple_token(apple_access_token)
    email = apple_token["email"]
    username = apple_token["email"].split("@")[0]

    return await login_user_oauth(username, email, 4, db)


class AppleTokenRequest(BaseModel):
    """A Pydantic model representing a request to validate an Apple token."""

    access_token: str


@api_router_v1.post("/auth/apple/token", status_code=200)
async def login_apple_token(
    apple_token_request: AppleTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> SuccessfulLoginResponse:
    """Validates an Apple token and logs in the user."""
    user = await validate_apple_user(apple_token_request.access_token, db)
    user_token = get_user_tokens(user)
    db.add(user_token)
    await db.commit()
    return await get_successful_login_response(user_token, user, db)


@api_router_v1.get("/auth/apple")
async def apple_login() -> RedirectResponse:
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


def generate_token() -> str:
    """Generates a JWT token for Apple OAuth2 authentication."""
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


def decode_apple_token(token: str) -> Any:
    """Decodes an Apple OAuth token."""
    return pyjwt.decode(
        token,
        audience=settings.APPLE_CLIENT_ID,
        options={"verify_signature": False},
    )


@api_router_v1.post("/auth/callback/apple")
async def apple_callback(
    code: Annotated[str, Form()],
    state: Annotated[str, Form()],
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """Handle Apple OAuth2 callback"""
    await validate_oauth_state(state)
    apple_key_url = settings.APPLE_AUTHORIZE_TOKEN
    async with httpx.AsyncClient() as client:
        userinfo_response = await client.post(
            apple_key_url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "client_id": settings.APPLE_CLIENT_ID,
                "client_secret": generate_token(),
                "code": code,
                "grant_type": settings.APPLE_GRANT_TYPE,
                "redirect_uri": settings.APPLE_REDIRECT_URL,
            },
            timeout=30,
        )

        user_info = userinfo_response.json()
        if (
            not user_info.get("access_token")
            or not user_info.get("refresh_token")
            or not user_info.get("id_token")
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="There was an error creating the user",
            )

        apple_access_token = user_info["id_token"]

        user = await validate_apple_user(apple_access_token, db)
        user_token = get_user_tokens(user, 120, 120)
        db.add(user_token)
        await db.commit()

        return redirect_oauth(user_token.access_token)
