"""Test for apple oauth endpoints direct."""

from typing import Any
from unittest.mock import AsyncMock, patch
from urllib.parse import quote

import pytest
from fakeredis import FakeRedis
from fastapi import HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.oauth import apple_oauth
from src.config.config import settings
from src.models.user import User
from src.util.util import SuccessfulLoginResponse, LoginData
from tests.conftest import add_token, add_user
from tests.helpers import AsyncFakeRedis


def test_generate_token() -> None:
    """Test that generate_token returns a valid JWT."""
    token: str = apple_oauth.generate_token()
    assert isinstance(token, str)
    assert token != ""


def test_decode_apple_token() -> None:
    """Test that decode_apple_token decodes a token correctly."""
    test_token: str = "test_token"
    with patch("jwt.decode") as mock_decode:
        mock_decode.return_value = {"email": "test@example.com"}
        result: dict[str, Any] = apple_oauth.decode_apple_token(test_token)
        assert result == {"email": "test@example.com"}


@pytest.mark.asyncio
async def test_apple_callback_flow_direct(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    test_user = await add_user("test_user_apple", 4, test_db)
    await test_db.refresh(test_user)
    test_user, _ = await add_token(1000, 1000, test_db, test_user.id)
    fake_redis_sync = FakeRedis()
    fake_redis = AsyncFakeRedis(fake_redis_sync)

    test_state: str = "test_state"
    fake_redis_sync.set(f"oauth_state:{test_state}", "1")

    class MockPostResponse:
        @staticmethod
        def json() -> dict[str, str]:
            return {
                "access_token": "fake_access_token",
                "refresh_token": "fake_refresh_token",
                "id_token": "fake_id_token",
            }

    mock_decoded_token: dict[str, str] = {
        "email": "test_user_apple@example.com",
    }
    mock_encoded_token: str = "return_token_apple"
    mock_access_token: str = "return_access_token"

    with (
        patch("src.api.api_v1.oauth.login_oauth.redis", fake_redis),
        patch(
            "src.api.api_v1.oauth.apple_oauth.httpx.AsyncClient.post",
            new_callable=AsyncMock,
        ) as mock_post,
        patch("src.api.api_v1.oauth.apple_oauth.pyjwt.encode") as mock_encode,
        patch("src.api.api_v1.oauth.apple_oauth.pyjwt.decode") as mock_decode,
        patch("src.models.User.generate_auth_token") as mock_generate_auth_token,
    ):
        mock_post.return_value = MockPostResponse
        mock_decode.return_value = mock_decoded_token
        mock_encode.return_value = mock_encoded_token
        mock_generate_auth_token.return_value = mock_access_token

        response: RedirectResponse = await apple_oauth.apple_callback(
            code="test_code",
            state=test_state,
            db=test_db,
        )

        mock_post.assert_called_once_with(
            settings.APPLE_AUTHORIZE_TOKEN,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "client_id": settings.APPLE_CLIENT_ID,
                "client_secret": apple_oauth.generate_token(),
                "code": "test_code",
                "grant_type": settings.APPLE_GRANT_TYPE,
                "redirect_uri": settings.APPLE_REDIRECT_URL,
            },
            timeout=30,
        )

        mock_decode.assert_called_once_with(
            MockPostResponse().json()["id_token"],
            audience=settings.APPLE_CLIENT_ID,
            options={"verify_signature": False},
        )

        assert isinstance(response, RedirectResponse)
        assert response.status_code == 303
        assert (
            response.headers["location"]
            == f"{settings.FRONTEND_URL}/auth/callback?token={mock_access_token}"
        )


@pytest.mark.asyncio
async def test_apple_login_endpoint_direct(test_setup: TestClient) -> None:
    fake_redis_sync = FakeRedis()
    fake_redis = AsyncFakeRedis(fake_redis_sync)

    fixed_state: str = "fixed_state_for_testing"

    mock_auth_url: str = "https://appleid.apple.com/auth/authorize"
    mock_client_id: str = "your_client_id"
    mock_redirect_uri: str = "https://your-redirect-uri.com/callback"
    mock_oauth_lifetime: int = 3600

    with (
        patch("src.api.api_v1.oauth.apple_oauth.redis", fake_redis),
        patch(
            "src.api.api_v1.oauth.apple_oauth.secrets.token_urlsafe",
            return_value=fixed_state,
        ),
        patch(
            "src.api.api_v1.oauth.apple_oauth.settings.APPLE_AUTHORIZE", mock_auth_url
        ),
        patch(
            "src.api.api_v1.oauth.apple_oauth.settings.APPLE_CLIENT_ID", mock_client_id
        ),
        patch(
            "src.api.api_v1.oauth.apple_oauth.settings.APPLE_REDIRECT_URL",
            mock_redirect_uri,
        ),
        patch(
            "src.api.api_v1.oauth.apple_oauth.settings.OAUTH_LIFETIME",
            mock_oauth_lifetime,
        ),
    ):
        response: RedirectResponse = await apple_oauth.apple_login()

        assert isinstance(response, RedirectResponse)
        assert response.status_code == 307

        encoded_redirect_uri: str = quote(
            "https://your-redirect-uri.com/callback", safe=""
        )
        expected_url: str = (
            f"{mock_auth_url}?"
            f"response_type=code+id_token&"
            f"client_id={mock_client_id}&"
            f"redirect_uri={encoded_redirect_uri}&"
            f"state={fixed_state}&"
            f"scope=name+email&"
            f"response_mode=form_post"
        )
        assert response.headers["location"] == expected_url

        assert await fake_redis.exists(f"oauth_state:{fixed_state}")
        ttl: int = await fake_redis.ttl(f"oauth_state:{fixed_state}")
        assert ttl <= mock_oauth_lifetime


@pytest.mark.asyncio
async def test_apple_callback_missing_tokens(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    fake_redis_sync = FakeRedis()
    fake_redis = AsyncFakeRedis(fake_redis_sync)
    test_state: str = "test_state"
    fake_redis_sync.set(f"oauth_state:{test_state}", "1")

    class MockPostResponse:
        @staticmethod
        def json() -> dict[Any, Any]:
            return {}

    with (
        patch("src.api.api_v1.oauth.login_oauth.redis", fake_redis),
        patch(
            "src.api.api_v1.oauth.apple_oauth.httpx.AsyncClient.post",
            new_callable=AsyncMock,
        ) as mock_post,
    ):
        mock_post.return_value = MockPostResponse

        with pytest.raises(HTTPException) as exc_info:
            await apple_oauth.apple_callback(
                code="test_code",
                state=test_state,
                db=test_db,
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "There was an error creating the user"


@pytest.mark.asyncio
async def test_login_apple_token_direct(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    test_user = await add_user("test_user_apple_token", 1, test_db)
    await test_db.refresh(test_user)
    test_user, test_token = await add_token(1000, 1000, test_db, test_user.id)

    async def mock_validate_apple_user(access_token: str, db: AsyncSession) -> User:
        return test_user

    mock_response = SuccessfulLoginResponse(
        success=True,
        data=LoginData(
            access_token=test_token.access_token,
            refresh_token=test_token.refresh_token,
            profile_version=1,
            avatar_version=1,
            friends=[],
        ),
    )

    with (
        patch(
            "src.api.api_v1.oauth.apple_oauth.validate_apple_user",
            new=mock_validate_apple_user,
        ),
        patch(
            "src.api.api_v1.oauth.apple_oauth.get_successful_login_response",
            return_value=mock_response,
        ),
    ):
        response = await apple_oauth.login_apple_token(
            apple_token_request=apple_oauth.AppleTokenRequest(
                access_token="fake_access_token"
            ),
            db=test_db,
        )
        assert response == mock_response
