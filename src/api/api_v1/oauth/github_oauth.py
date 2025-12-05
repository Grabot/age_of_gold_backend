"""Handler for the Github oauth2 flow"""

import secrets
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


@api_router_v1.get("/auth/github")
async def github_login() -> RedirectResponse:
    """Start Github OAuth2 login"""
    state = secrets.token_urlsafe(16)
    await redis.setex(f"oauth_state:{state}", settings.OAUTH_LIFETIME, "valid")
    auth_url = "https://github.com/login/oauth/authorize"
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "state": state,
        "redirect_uri": settings.GITHUB_REDIRECT_URL,
    }

    url_params = urlencode(params)
    authorization_url = auth_url + "?" + url_params

    return RedirectResponse(url=authorization_url)


async def _fetch_github_access_token(code: str) -> str:
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "client_secret": settings.GITHUB_CLIENT_SECRET,
        "code": code,
        "redirect_uri": settings.GITHUB_REDIRECT_URL,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://github.com/login/oauth/access_token",
            params=params,
            headers={"Accept": "application/json"},
            timeout=10,
        )
        response_dict: dict[str, str] = response.json()
        return response_dict["access_token"]


async def _fetch_github_user(access_token: str) -> dict[str, str]:
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(
            settings.GITHUB_USER,
            headers=headers,
            timeout=10,
        )
        response_dict: dict[str, str] = response.json()
        return response_dict


@api_router_v1.get("/auth/callback/github")
async def github_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """Handle GitHub OAuth2 callback"""
    await validate_oauth_state(state)

    access_token = await _fetch_github_access_token(code)
    github_user = await _fetch_github_user(access_token)

    username = github_user["login"]
    email = github_user["email"]
    user = await login_user_oauth(username, email, 2, db)
    user_token = get_user_tokens(user, 120, 120)
    db.add(user_token)
    await db.commit()
    return redirect_oauth(user_token.access_token)
