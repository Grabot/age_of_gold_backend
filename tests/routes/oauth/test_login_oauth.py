"""Test for login oauth fuctionality."""

from unittest.mock import AsyncMock, patch

import pytest
from fakeredis import FakeRedis
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.oauth import login_oauth
from src.models.user import User, hash_email
from tests.helpers import AsyncFakeRedis


@pytest.mark.asyncio
async def test_validate_oauth_state_exists() -> None:
    fake_redis_sync: FakeRedis = FakeRedis()
    fake_redis: AsyncFakeRedis = AsyncFakeRedis(fake_redis_sync)

    test_state: str = "test_state"
    fake_redis_sync.set(f"oauth_state:{test_state}", "1")

    with patch("src.api.api_v1.oauth.login_oauth.redis", fake_redis):
        await login_oauth.validate_oauth_state(test_state)

        assert fake_redis_sync.exists(f"oauth_state:{test_state}") == 0


@pytest.mark.asyncio
async def test_validate_oauth_state_does_not_exist() -> None:
    fake_redis_sync: FakeRedis = FakeRedis()
    fake_redis: AsyncFakeRedis = AsyncFakeRedis(fake_redis_sync)

    test_state: str = "test_state_fail"
    with patch("src.api.api_v1.oauth.login_oauth.redis", fake_redis):
        with pytest.raises(HTTPException) as exc_info:
            await login_oauth.validate_oauth_state(test_state)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Invalid state"

        assert fake_redis_sync.exists(f"oauth_state:{test_state}") == 0


def test_sanitize_username_with_email() -> None:
    email_username: str = "test@example.com"
    sanitized: str = login_oauth._sanitize_username(email_username)
    assert sanitized == "testexample.com"


def test_sanitize_username_without_email() -> None:
    normal_username: str = "test_user"
    sanitized: str = login_oauth._sanitize_username(normal_username)
    assert sanitized == "test_user"


@pytest.mark.asyncio
async def test_find_available_username_available(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    username: str = await login_oauth._find_available_username(
        test_db, "test_user_login"
    )
    assert username == "test_user_login"


@pytest.mark.asyncio
async def test_find_available_username_taken(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    login_user: User = User(
        username="test_user_login_available",
        email_hash="test_user_login_available@example.com",
        password_hash="",
        salt="",
        origin=0,
    )
    test_db.add(login_user)
    await test_db.commit()
    username: str = await login_oauth._find_available_username(
        test_db, "test_user_login_available"
    )
    assert username == "test_user_login_available_2"


@pytest.mark.asyncio
async def test_find_available_username_all_taken(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    test_db.add(
        User(
            username="test_user_login_taken",
            email_hash="test_user_login_taken@example.com",
            password_hash="",
            salt="",
            origin=0,
        )
    )
    for i in range(2, 101):
        test_db.add(
            User(
                username=f"test_user_login_taken_{i}",
                email_hash="test_user_login_taken@example.com",
                password_hash="",
                salt="",
                origin=0,
            )
        )
    await test_db.commit()

    with pytest.raises(HTTPException) as exc_info:
        await login_oauth._find_available_username(test_db, "test_user_login_taken")

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "Couldn't create the user"


@pytest.mark.asyncio
async def test_create_user(test_setup: TestClient, test_db: AsyncSession) -> None:
    new_username: str = "test_user_login_create"
    new_hashed_email: str = hash_email("test_user_login_create@example.com")
    user: User | None
    created: bool
    user, created = await login_oauth._create_user(
        test_db, new_username, new_hashed_email, 1
    )

    assert user.username == new_username
    assert user.email_hash == new_hashed_email
    assert user.origin == 1
    assert created is True


@pytest.mark.asyncio
async def test_login_user_oauth_existing_user(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    test_user_login: str = "test_user_login"
    test_email: str = "test_user_login@example.com"
    test_origin: int = 1
    login_user: User = User(
        username=test_user_login,
        email_hash=hash_email(test_email),
        password_hash="",
        salt="",
        origin=test_origin,
    )
    test_db.add(login_user)
    await test_db.commit()

    return_user = await login_oauth.login_user_oauth(
        test_user_login, test_email, test_origin, test_db
    )
    assert login_user == return_user


@pytest.mark.asyncio
async def test_login_user_oauth_new_user(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    test_username: str = "test_user"
    test_email: str = "test@example.com"
    test_origin: int = 1
    login_user: User = User(
        id=11,
        username=test_username,
        email_hash=hash_email(test_email),
        password_hash="",
        salt="",
        origin=test_origin,
    )
    with (
        patch(
            "src.api.api_v1.oauth.login_oauth._create_user", new_callable=AsyncMock
        ) as mock_create,
        patch(
            "src.api.api_v1.oauth.login_oauth.task_generate_avatar.delay"
        ) as mock_avatar_task,
        patch.object(test_db, "refresh", new_callable=AsyncMock) as mock_refresh,
    ):
        mock_create.return_value = (login_user, True)

        return_user = await login_oauth.login_user_oauth(
            test_username, test_email, test_origin, test_db
        )

        mock_refresh.assert_called_once_with(login_user)
        assert login_user == return_user
        mock_avatar_task.assert_called_once_with(
            login_user.avatar_filename(), login_user.id
        )


@pytest.mark.asyncio
async def test_login_user_oauth_user_creation_failed(
    test_setup: TestClient, test_db: AsyncSession
) -> None:
    test_username: str = "test_user"
    test_email: str = "test@example.com"
    test_origin: int = 1

    with patch(
        "src.api.api_v1.oauth.login_oauth._create_user", new_callable=AsyncMock
    ) as mock_create:
        mock_create.return_value = (None, False)

        with pytest.raises(HTTPException) as exc_info:
            await login_oauth.login_user_oauth(
                test_username, test_email, test_origin, test_db
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "User creation failed"
