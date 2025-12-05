"""Test for Google oauth endpoints direct."""

from unittest.mock import AsyncMock, patch
from urllib.parse import quote

import pytest
from fakeredis import FakeRedis
from fastapi import HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.oauth import google_oauth
from src.config.config import settings
from src.models.user import User
from src.util.util import SuccessfulLoginResponse, UserTokenData
from tests.conftest import add_token, add_user
from tests.helpers import AsyncFakeRedis


@pytest.mark.asyncio
async def test_google_callback_flow_direct(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    test_user = await add_user("test_user_google", 1, test_db)
    await test_db.refresh(test_user)
    test_user, _ = await add_token(1000, 1000, test_db, test_user.id)

    fake_redis_sync = FakeRedis()
    fake_redis = AsyncFakeRedis(fake_redis_sync)
    test_state = "test_state"
    fake_redis_sync.set(f"oauth_state:{test_state}", "1")

    mock_access_token = "return_access_token"

    class MockPostResponse:
        @staticmethod
        def json() -> dict[str, str]:
            return {
                "access_token": "fake_access_token",
                "refresh_token": "fake_refresh_token",
                "id_token": "fake_id_token",
            }

    class MockGetResponse:
        status_code = 200

        @staticmethod
        def json() -> dict[str, bool | str]:
            return {
                "email": "test_user_google@example.com",
                "email_verified": True,
                "given_name": "TestUser",
            }

    with (
        patch("src.api.api_v1.oauth.login_oauth.redis", fake_redis),
        patch(
            "src.api.api_v1.oauth.google_oauth.httpx.AsyncClient.post",
            new_callable=AsyncMock,
        ) as mock_post,
        patch(
            "src.api.api_v1.oauth.google_oauth.httpx.AsyncClient.get",
            new_callable=AsyncMock,
        ) as mock_get,
        patch("src.models.User.generate_auth_token") as mock_generate_auth_token,
    ):
        mock_post.return_value = MockPostResponse
        mock_get.return_value = MockGetResponse
        mock_generate_auth_token.return_value = mock_access_token

        response = await google_oauth.google_callback(
            code="test_code",
            state=test_state,
            db=test_db,
        )

        mock_post.assert_called_once_with(
            settings.GOOGLE_AUTHORIZE,
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "code": "test_code",
                "grant_type": "authorization_code",
                "redirect_uri": settings.GOOGLE_REDIRECT_URL,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        mock_get.assert_called_once_with(
            settings.GOOGLE_ACCESS_TOKEN_URL,
            headers={"Authorization": "Bearer fake_access_token"},
        )

        assert isinstance(response, RedirectResponse)
        assert response.status_code == 303
        assert (
            response.headers["location"]
            == f"{settings.FRONTEND_URL}/auth/callback?token={mock_access_token}"
        )


@pytest.mark.asyncio
async def test_google_login_endpoint_direct(test_setup: TestClient) -> None:
    fake_redis_sync = FakeRedis()
    fake_redis = AsyncFakeRedis(fake_redis_sync)
    fixed_state = "fixed_state_for_testing"

    mock_auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
    mock_client_id = "your_google_client_id"
    mock_redirect_uri = "https://your-google-redirect-uri.com/callback"
    mock_oauth_lifetime = 3600

    with (
        patch("src.api.api_v1.oauth.google_oauth.redis", fake_redis),
        patch(
            "src.api.api_v1.oauth.google_oauth.secrets.token_urlsafe",
            return_value=fixed_state,
        ),
        patch(
            "src.api.api_v1.oauth.google_oauth.settings.GOOGLE_ACCOUNTS_URL",
            mock_auth_url,
        ),
        patch(
            "src.api.api_v1.oauth.google_oauth.settings.GOOGLE_CLIENT_ID",
            mock_client_id,
        ),
        patch(
            "src.api.api_v1.oauth.google_oauth.settings.GOOGLE_REDIRECT_URL",
            mock_redirect_uri,
        ),
        patch(
            "src.api.api_v1.oauth.google_oauth.settings.OAUTH_LIFETIME",
            mock_oauth_lifetime,
        ),
    ):
        response = await google_oauth.google_login()

        # Assertions
        assert isinstance(response, RedirectResponse)
        assert response.status_code == 307  # Temporary Redirect

        # Construct the expected URL with Google's parameters
        encoded_redirect_uri = quote(mock_redirect_uri, safe="")
        expected_url = (
            f"{mock_auth_url}?"
            f"client_id={mock_client_id}&"
            f"redirect_uri={encoded_redirect_uri}&"
            f"response_type=code&"
            f"scope=email+profile&"
            f"access_type=offline&"
            f"prompt=consent&"
            f"state={fixed_state}"
        )
        assert response.headers["location"] == expected_url

        # Verify Redis state was set
        assert await fake_redis.exists(f"oauth_state:{fixed_state}")
        ttl = await fake_redis.ttl(f"oauth_state:{fixed_state}")
        assert ttl <= mock_oauth_lifetime


@pytest.mark.asyncio
async def test_google_callback_token_error(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    fake_redis_sync = FakeRedis()
    fake_redis = AsyncFakeRedis(fake_redis_sync)
    test_state = "test_state"
    fake_redis_sync.set(f"oauth_state:{test_state}", "1")

    class MockErrorPostResponse:
        @staticmethod
        def json() -> dict[str, str]:
            return {"error": "invalid_grant", "error_description": "Invalid code"}

    with (
        patch("src.api.api_v1.oauth.login_oauth.redis", fake_redis),
        patch(
            "src.api.api_v1.oauth.google_oauth.httpx.AsyncClient.post",
            new_callable=AsyncMock,
        ) as mock_post,
    ):
        mock_post.return_value = MockErrorPostResponse()

        with pytest.raises(HTTPException) as exc_info:
            await google_oauth.google_callback(
                code="test_code",
                state=test_state,
                db=test_db,
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            "Error getting Google access token: Invalid code" in exc_info.value.detail
        )


@pytest.mark.asyncio
async def test_google_callback_userinfo_failure(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    fake_redis_sync = FakeRedis()
    fake_redis = AsyncFakeRedis(fake_redis_sync)
    test_state = "test_state"
    fake_redis_sync.set(f"oauth_state:{test_state}", "1")

    class MockPostResponse:
        @staticmethod
        def json() -> dict[str, str]:
            return {"access_token": "fake_access_token"}

    class MockFailedGetResponse:
        status_code = 401  # Simulate a failed request

    with (
        patch("src.api.api_v1.oauth.login_oauth.redis", fake_redis),
        patch(
            "src.api.api_v1.oauth.google_oauth.httpx.AsyncClient.post",
            new_callable=AsyncMock,
        ) as mock_post,
        patch(
            "src.api.api_v1.oauth.google_oauth.httpx.AsyncClient.get",
            new_callable=AsyncMock,
        ) as mock_get,
    ):
        mock_post.return_value = MockPostResponse()
        mock_get.return_value = MockFailedGetResponse()

        with pytest.raises(HTTPException) as exc_info:
            await google_oauth.google_callback(
                code="test_code",
                state=test_state,
                db=test_db,
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Failed to fetch user info"


@pytest.mark.asyncio
async def test_google_callback_unverified_email(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    fake_redis_sync = FakeRedis()
    fake_redis = AsyncFakeRedis(fake_redis_sync)
    test_state = "test_state"
    fake_redis_sync.set(f"oauth_state:{test_state}", "1")

    class MockPostResponse:
        @staticmethod
        def json() -> dict[str, str]:
            return {"access_token": "fake_access_token"}

    class MockUnverifiedGetResponse:
        status_code = 200

        @staticmethod
        def json() -> dict[str, bool | str]:
            return {
                "email": "test_user_google@example.com",
                "email_verified": False,
                "given_name": "TestUser",
            }

    with (
        patch("src.api.api_v1.oauth.login_oauth.redis", fake_redis),
        patch(
            "src.api.api_v1.oauth.google_oauth.httpx.AsyncClient.post",
            new_callable=AsyncMock,
        ) as mock_post,
        patch(
            "src.api.api_v1.oauth.google_oauth.httpx.AsyncClient.get",
            new_callable=AsyncMock,
        ) as mock_get,
    ):
        mock_post.return_value = MockPostResponse()
        mock_get.return_value = MockUnverifiedGetResponse()

        with pytest.raises(HTTPException) as exc_info:
            await google_oauth.google_callback(
                code="test_code",
                state=test_state,
                db=test_db,
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Email not verified"


@pytest.mark.asyncio
async def test_login_google_token_direct(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    test_user = await add_user("test_user_google_token", 1, test_db)
    await test_db.refresh(test_user)
    test_user, test_token = await add_token(1000, 1000, test_db, test_user.id)

    async def mock_validate_google_user(access_token: str, db: AsyncSession) -> User:
        return test_user

    mock_response = SuccessfulLoginResponse(
        success=True,
        data=UserTokenData(
            access_token=test_token.access_token,
            refresh_token=test_token.refresh_token,
            profile_version=1,
            avatar_version=1,
        ),
    )

    with (
        patch(
            "src.api.api_v1.oauth.google_oauth.validate_google_user",
            new=mock_validate_google_user,
        ),
        patch(
            "src.api.api_v1.oauth.google_oauth.get_successful_login_response",
            return_value=mock_response,
        ),
    ):
        response = await google_oauth.login_google_token(
            google_token_request=google_oauth.GoogleTokenRequest(
                access_token="fake_access_token"
            ),
            db=test_db,
        )
        assert response == mock_response
