"""Test for GitHub oauth endpoints direct."""

from unittest.mock import AsyncMock, patch
from fastapi.responses import RedirectResponse
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.api_v1.oauth import github_oauth
from tests.conftest import add_token, add_user
from src.config.config import settings
from fakeredis import FakeRedis
from tests.helpers import AsyncFakeRedis


@pytest.mark.asyncio
async def test_github_callback_flow_direct(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    test_user = await add_user("test_user_github", 2, test_db)
    await test_db.refresh(test_user)
    test_user, _ = await add_token(1000, 1000, test_db, test_user.id)

    fake_redis_sync = FakeRedis()
    fake_redis = AsyncFakeRedis(fake_redis_sync)
    test_state = "test_state"
    fake_redis_sync.set(f"oauth_state:{test_state}", "1")

    class MockPostResponse:
        status_code = 200

        @staticmethod
        def json() -> dict[str, str]:
            return {"access_token": "fake_access_token"}

    class MockGetResponse:
        status_code = 200

        @staticmethod
        def json() -> dict[str, str]:
            return {
                "login": "test_user_github",
                "email": "test_user_github@example.com",
            }

    mock_post_response = MockPostResponse()
    mock_get_response = MockGetResponse()
    mock_access_token = "return_access_token"

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
        mock_post.return_value = mock_post_response
        mock_get.return_value = mock_get_response
        mock_generate_auth_token.return_value = mock_access_token

        response = await github_oauth.github_callback(
            code="test_code",
            state=test_state,
            db=test_db,
        )

        mock_post.assert_called_once_with(
            "https://github.com/login/oauth/access_token",
            params={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": "test_code",
            },
            headers={"Accept": "application/json"},
            timeout=10,
        )

        mock_get.assert_called_once_with(
            settings.GITHUB_USER,
            headers={
                "Accept": "application/json",
                "Authorization": "Bearer fake_access_token",
            },
            timeout=10,
        )

        # Assert the response
        assert isinstance(response, RedirectResponse)
        assert response.status_code == 303
        assert (
            response.headers["location"]
            == f"{settings.FRONTEND_URL}/auth/callback?token={mock_access_token}"
        )


@pytest.mark.asyncio
async def test_github_login_endpoint_direct(test_setup: TestClient) -> None:
    fake_redis_sync = FakeRedis()
    fake_redis = AsyncFakeRedis(fake_redis_sync)
    fixed_state = "fixed_state_for_testing"

    mock_auth_url = "https://github.com/login/oauth/authorize"
    mock_client_id = "your_github_client_id"
    mock_oauth_lifetime = 3600

    with (
        patch("src.api.api_v1.oauth.github_oauth.redis", fake_redis),
        patch(
            "src.api.api_v1.oauth.github_oauth.secrets.token_urlsafe",
            return_value=fixed_state,
        ),
        patch(
            "src.api.api_v1.oauth.github_oauth.settings.GITHUB_CLIENT_ID",
            mock_client_id,
        ),
        patch(
            "src.api.api_v1.oauth.github_oauth.settings.OAUTH_LIFETIME",
            mock_oauth_lifetime,
        ),
    ):
        response = await github_oauth.github_login()

        assert isinstance(response, RedirectResponse)
        assert response.status_code == 307

        expected_url = (
            f"{mock_auth_url}/?client_id={mock_client_id}&state={fixed_state}"
        )
        assert response.headers["location"] == expected_url

        assert await fake_redis.exists(f"oauth_state:{fixed_state}")
        ttl = await fake_redis.ttl(f"oauth_state:{fixed_state}")
        assert ttl <= mock_oauth_lifetime
