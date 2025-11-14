import secrets
from urllib.parse import urlencode
from fastapi.responses import RedirectResponse
from src.api.api_v1.oauth.login_oauth import login_user_oauth
from src.api.api_v1.router import api_router_v1
from fastapi import Depends, HTTPException, status
from src.config.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.sockets.sockets import redis
import requests


@api_router_v1.get("/auth/github")
async def github_login():
    """Start Github OAuth2 login"""
    state = secrets.token_urlsafe(16)
    await redis.setex(f"oauth_state:{state}", settings.OAUTH_LIFETIME, "valid")
    auth_url = "https://github.com/login/oauth/authorize"
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "state": state,
    }

    url_params = urlencode(params)
    authorization_url = auth_url + "/?" + url_params

    return RedirectResponse(url=authorization_url)


@api_router_v1.get("/auth/callback/github")
async def github_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    """Handle Github OAuth2 callback"""
    if not await redis.exists(f"oauth_state:{state}"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state"
        )
    await redis.delete(f"oauth_state:{state}")
    # TODO: from settings?
    access_base_url = "https://github.com/login/oauth/access_token"
    params = dict()
    params["client_id"] = settings.GITHUB_CLIENT_ID
    params["client_secret"] = settings.GITHUB_CLIENT_SECRET
    params["code"] = code

    url_params = urlencode(params)
    github_post_url = access_base_url + "/?" + url_params

    headers = {
        "Accept": "application/json",
    }
    token_response = requests.post(github_post_url, headers=headers)

    github_response_json = token_response.json()

    headers_authorization = {
        "Accept": "application/json",
        "Authorization": "Bearer %s" % github_response_json["access_token"],
    }
    authorization_url = settings.GITHUB_USER

    authorization_response = requests.get(
        authorization_url, headers=headers_authorization
    )

    github_user = authorization_response.json()

    username = github_user["login"]
    email = github_user["email"]

    return login_user_oauth(username, email, 2, db)
