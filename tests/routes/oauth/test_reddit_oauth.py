"""Test for Reddit oauth endpoints direct."""

from base64 import b64encode
from unittest.mock import AsyncMock, patch
from urllib.parse import quote
from fastapi.responses import RedirectResponse
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.oauth import reddit_oauth
from tests.conftest import add_token, add_user

from src.config.config import settings
from fakeredis import FakeRedis

from tests.helpers import AsyncFakeRedis


@pytest.mark.asyncio
async def test_reddit_callback_flow_direct(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    test_user = await add_user("test_user_reddit", 3, test_db, "reddit.com")
    await test_db.refresh(test_user)
    test_user, _ = await add_token(1000, 1000, test_db, test_user.id)

    fake_redis_sync: FakeRedis = FakeRedis()
    fake_redis: AsyncFakeRedis = AsyncFakeRedis(fake_redis_sync)
    test_state: str = "test_state"
    fake_redis_sync.set(f"oauth_state:{test_state}", "1")

    class MockPostResponse:
        status_code: int = 200

        @staticmethod
        def json() -> dict[str, str]:
            return {"access_token": "fake_access_token"}

    class MockGetResponse:
        status_code: int = 200

        @staticmethod
        def json() -> dict[str, str]:
            return {"name": "test_user_reddit"}

    mock_post_response: MockPostResponse = MockPostResponse()
    mock_get_response: MockGetResponse = MockGetResponse()
    mock_access_token: str = "return_access_token"

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

        response: RedirectResponse = await reddit_oauth.reddit_callback(
            code="test_code",
            state=test_state,
            db=test_db,
        )

        encoded_authorization: str = (
            f"{settings.REDDIT_CLIENT_ID}:{settings.REDDIT_CLIENT_SECRET}"
        )
        http_auth: str = b64encode(encoded_authorization.encode("utf-8")).decode(
            "utf-8"
        )
        mock_post.assert_called_once_with(
            settings.REDDIT_ACCESS,
            headers={
                "Accept": "application/json",
                "User-agent": "age of gold login bot 0.1",
                "Authorization": f"Basic {http_auth}",
            },
            data={
                "grant_type": "authorization_code",
                "code": "test_code",
                "redirect_uri": settings.REDDIT_REDIRECT,
            },
            timeout=30,
        )

        mock_get.assert_called_once_with(
            settings.REDDIT_USER,
            headers={
                "Accept": "application/json",
                "User-agent": "age of gold login bot 0.1",
                "Authorization": "Bearer fake_access_token",
            },
            timeout=30,
        )

        assert isinstance(response, RedirectResponse)
        assert response.status_code == 303
        assert (
            response.headers["location"]
            == f"{settings.FRONTEND_URL}/auth/callback?token={mock_access_token}"
        )


@pytest.mark.asyncio
async def test_reddit_login_endpoint_direct(test_setup: TestClient) -> None:
    fake_redis_sync: FakeRedis = FakeRedis()
    fake_redis: AsyncFakeRedis = AsyncFakeRedis(fake_redis_sync)
    fixed_state: str = "fixed_state_for_testing"

    # Reddit-specific mock settings
    mock_auth_url: str = "https://www.reddit.com/api/v1/authorize"
    mock_client_id: str = "your_reddit_client_id"
    mock_redirect_uri: str = "https://your-reddit-redirect-uri.com/callback"
    mock_oauth_lifetime: int = 3600

    with (
        patch("src.api.api_v1.oauth.reddit_oauth.redis", fake_redis),
        patch(
            "src.api.api_v1.oauth.reddit_oauth.secrets.token_urlsafe",
            return_value=fixed_state,
        ),
        patch(
            "src.api.api_v1.oauth.reddit_oauth.settings.REDDIT_AUTHORIZE", mock_auth_url
        ),
        patch(
            "src.api.api_v1.oauth.reddit_oauth.settings.REDDIT_CLIENT_ID",
            mock_client_id,
        ),
        patch(
            "src.api.api_v1.oauth.reddit_oauth.settings.REDDIT_REDIRECT",
            mock_redirect_uri,
        ),
        patch(
            "src.api.api_v1.oauth.reddit_oauth.settings.OAUTH_LIFETIME",
            mock_oauth_lifetime,
        ),
    ):
        response: RedirectResponse = await reddit_oauth.reddit_login()

        # Assertions
        assert isinstance(response, RedirectResponse)
        assert response.status_code == 307  # Temporary Redirect

        # Construct the expected URL with Reddit's parameters
        encoded_redirect_uri: str = quote(mock_redirect_uri, safe="")
        expected_url: str = (
            f"{mock_auth_url}/?"
            f"client_id={mock_client_id}&"
            f"redirect_uri={encoded_redirect_uri}&"
            f"response_type=code&"
            f"scope=identity&"
            f"duration=temporary&"
            f"state={fixed_state}"
        )
        assert response.headers["location"] == expected_url

        # Verify Redis state was set
        assert await fake_redis.exists(f"oauth_state:{fixed_state}")
        ttl: int = await fake_redis.ttl(f"oauth_state:{fixed_state}")
        assert ttl <= mock_oauth_lifetime
