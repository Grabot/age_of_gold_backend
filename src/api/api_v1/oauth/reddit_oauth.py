"""Handler for the Reddit oauth2 flow"""

import secrets
from base64 import b64encode
from urllib.parse import urlencode

import httpx
from fastapi import Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.oauth.login_oauth import (
    login_user_oauth,
    redirect_oauth,
    validate_oauth_state,
)
from src.api.api_v1.router import api_router_v1
from src.config.config import settings
from src.database import get_db
from src.sockets.sockets import redis
from src.util.util import get_user_tokens


@api_router_v1.get("/auth/reddit")
async def reddit_login() -> RedirectResponse:
    """Start Reddit OAuth2 login"""
    state = secrets.token_urlsafe(16)
    await redis.setex(f"oauth_state:{state}", settings.OAUTH_LIFETIME, "valid")
    auth_url = settings.REDDIT_AUTHORIZE
    params = {
        "client_id": settings.REDDIT_CLIENT_ID,
        "redirect_uri": settings.REDDIT_REDIRECT_URL,
        "response_type": "code",
        "scope": "identity",
        "duration": "temporary",
        "state": state,
    }

    url_params = urlencode(params)
    authorization_url = auth_url + "/?" + url_params

    return RedirectResponse(url=authorization_url)


async def _fetch_reddit_access_token(code: str) -> str:
    """Fetch the Reddit access token."""
    access_base_url = settings.REDDIT_ACCESS
    token_post_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.REDDIT_REDIRECT_URL,
    }

    encoded_authorization = (
        f"{settings.REDDIT_CLIENT_ID}:{settings.REDDIT_CLIENT_SECRET}"
    )
    http_auth = b64encode(encoded_authorization.encode("utf-8")).decode("utf-8")
    headers = {
        "Accept": "application/json",
        "User-agent": "age of gold login bot 0.1",
        "Authorization": f"Basic {http_auth}",
    }

    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            access_base_url, headers=headers, data=token_post_data, timeout=30
        )
        reddit_response_json: dict[str, str] = token_response.json()
        return reddit_response_json["access_token"]


async def _fetch_reddit_user(access_token: str) -> dict[str, str]:
    """Fetch the Reddit user information."""
    headers_authorization = {
        "Accept": "application/json",
        "User-agent": "age of gold login bot 0.1",
        "Authorization": f"Bearer {access_token}",
    }

    authorization_url = settings.REDDIT_USER
    async with httpx.AsyncClient() as client:
        authorization_response = await client.get(
            authorization_url, headers=headers_authorization, timeout=30
        )
        response_dict: dict[str, str] = authorization_response.json()
        return response_dict


@api_router_v1.get("/auth/callback/reddit")
async def reddit_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """Handle Reddit OAuth2 callback"""
    await validate_oauth_state(state)

    access_token = await _fetch_reddit_access_token(code)
    reddit_user = await _fetch_reddit_user(access_token)

    username = reddit_user["name"]
    email = f"{username}@reddit.com"  # Reddit does not provide an email

    user = await login_user_oauth(username, email, 3, db)
    user_token = get_user_tokens(user, 120, 120)
    db.add(user_token)
    await db.commit()
    return redirect_oauth(user_token.access_token)
