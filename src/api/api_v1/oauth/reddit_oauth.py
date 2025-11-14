from base64 import b64encode
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


@api_router_v1.get("/auth/reddit")
async def reddit_login():
    """Start Reddit OAuth2 login"""
    state = secrets.token_urlsafe(16)
    await redis.setex(f"oauth_state:{state}", settings.OAUTH_LIFETIME, "valid")
    auth_url = settings.REDDIT_AUTHORIZE
    params = {
        "client_id": settings.REDDIT_CLIENT_ID,
        "duration": "temporary",
        "redirect_uri": settings.REDDIT_REDIRECT,
        "response_type": "code",
        "scope": "identity",
        "state": state,
    }

    url_params = urlencode(params)
    authorization_url = auth_url + "/?" + url_params

    return RedirectResponse(url=authorization_url)


@api_router_v1.get("/auth/callback/reddit")
async def reddit_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    """Handle Reddit OAuth2 callback"""
    if not await redis.exists(f"oauth_state:{state}"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state"
        )
    await redis.delete(f"oauth_state:{state}")
    access_base_url = settings.REDDIT_ACCESS

    token_post_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.REDDIT_REDIRECT,
    }

    encoded_authorization = "%s:%s" % (
        settings.REDDIT_CLIENT_ID,
        settings.REDDIT_CLIENT_SECRET,
    )

    http_auth = b64encode(encoded_authorization.encode("utf-8")).decode("utf-8")
    authorization = "Basic %s" % http_auth
    headers = {
        "Accept": "application/json",
        "User-agent": "age of gold login bot 0.1",
        "Authorization": authorization,
    }

    token_response = requests.post(
        access_base_url, headers=headers, data=token_post_data
    )

    reddit_response_json = token_response.json()

    headers_authorization = {
        "Accept": "application/json",
        "User-agent": "age of gold login bot 0.1",
        "Authorization": "bearer %s" % reddit_response_json["access_token"],
    }
    authorization_url = settings.REDDIT_USER

    authorization_response = requests.get(
        authorization_url, headers=headers_authorization
    )

    reddit_user = authorization_response.json()

    username = reddit_user["name"]
    email = "%s@reddit.com" % username  # Reddit gives no email

    return login_user_oauth(username, email, 3, db)
