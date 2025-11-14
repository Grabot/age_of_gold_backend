import secrets
from urllib.parse import urlencode
from fastapi.responses import RedirectResponse
import requests
from src.api.api_v1.oauth.login_oauth import login_user_oauth
from src.api.api_v1.router import api_router_v1
from fastapi import Depends, Request
from fastapi import HTTPException, status
from src.config.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.sockets.sockets import redis
import httpx


@api_router_v1.get("/auth/google")
async def google_login():
    """Start Google OAuth2 login"""
    auth_url = settings.GOOGLE_ACCOUNTS_URL
    state = secrets.token_urlsafe(16)
    await redis.setex(f"oauth_state:{state}", settings.OAUTH_LIFETIME, "valid")
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "email profile",
        "access_type": "offline",
        "prompt": "consent",
        "state": state
    }

    url_params = urlencode(params)
    authorization_url = f"{auth_url}?{url_params}"

    return RedirectResponse(url=authorization_url)


@api_router_v1.get("/auth/callback/google")
async def google_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    """Handle Google OAuth2 callback"""
    if not await redis.exists(f"oauth_state:{state}"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state"
        )
    await redis.delete(f"oauth_state:{state}")

    token_url = settings.GOOGLE_AUTHORIZE
    data = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.GOOGLE_REDIRECT_URI
    }
    
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            token_url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        token_data = token_response.json()
        if "error" in token_data or "access_token" not in token_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error getting Google access token: {token_data.get('error_description', token_data['error'])}",
            )
        
        access_token = token_data["access_token"]
        userinfo_url = settings.GOOGLE_ACCESS_TOKEN_URL
        userinfo_response = await client.get(
            userinfo_url,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        if userinfo_response.status_code != 200:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to fetch user info")
        user_info = userinfo_response.json()
        if not user_info.get("email_verified"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email not verified")
        email = user_info["email"]
        username = user_info.get("given_name", "User")
        return await login_user_oauth(username, email, 1, db)
