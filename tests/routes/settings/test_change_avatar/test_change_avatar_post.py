"""Test for change username endpoint via direct get call."""

from io import BytesIO
from pathlib import Path
from unittest.mock import Mock
import pytest
from pytest_mock import MockerFixture
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status

from src.config.config import settings
from src.models.user import User
from tests.conftest import add_token


@pytest.mark.asyncio
async def test_successful_change_avatar_post(
    test_setup: TestClient, test_db: AsyncSession, mocker: MockerFixture
) -> None:
    """Test successful change avatar via direct HTTP call."""
    test_user, user_token = await add_token(1000, 1000, test_db)
    test_user_id = test_user.id
    test_user.default_avatar = False
    test_db.add(test_user)
    await test_db.commit()

    test_path = Path(__file__).parent.parent.parent.parent / "data"
    file_name = "test_default_copy"
    file_name_ext = file_name + ".png"
    full_path = test_path / file_name_ext
    assert full_path.is_file(), "Test avatar image must exist"

    with open(full_path, "rb") as f:
        file_content = f.read()
    file_like = BytesIO(file_content)

    mocker.patch.object(User, "create_avatar", new_callable=Mock)

    headers = {"Authorization": f"Bearer {user_token.access_token}"}
    response = test_setup.patch(
        f"{settings.API_V1_STR}/user/avatar",
        headers=headers,
        files={"avatar": (file_name_ext, file_like, "image/png")},
    )

    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert response_json["success"]
    test_user_result = await test_db.get(User, test_user_id)
    assert test_user_result is not None
    assert test_user_result.default_avatar is False


@pytest.mark.asyncio
async def test_successful_change_avatar_default_post(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful change avatar back to default via direct HTTP call."""
    test_user, user_token = await add_token(1000, 1000, test_db)
    test_user_id = test_user.id
    test_user.default_avatar = False
    test_db.add(test_user)
    await test_db.commit()

    headers = {"Authorization": f"Bearer {user_token.access_token}"}
    response = test_setup.patch(
        f"{settings.API_V1_STR}/user/avatar",
        headers=headers,
    )

    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert response_json["success"]
    test_user_result = await test_db.get(User, test_user_id)
    assert test_user_result is not None
    assert test_user_result.default_avatar


@pytest.mark.asyncio
async def test_change_avatar_invalid_file_post(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test that an invalid avatar file returns HTTP 400."""
    test_user, user_token = await add_token(1000, 1000, test_db)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}

    response = test_setup.patch(
        f"{settings.API_V1_STR}/user/avatar",
        headers=headers,
        files={"avatar": ("empty.txt", BytesIO(b""), "text/plain")},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Invalid avatar file"


@pytest.mark.asyncio
async def test_change_avatar_too_large_post(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test that an avatar file that is too large returns HTTP 400."""
    test_user, user_token = await add_token(1000, 1000, test_db)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}

    large_content = b"x" * (2 * 1024 * 1024 + 1)
    file_like = BytesIO(large_content)

    response = test_setup.patch(
        f"{settings.API_V1_STR}/user/avatar",
        headers=headers,
        files={"avatar": ("large_file.png", file_like, "image/png")},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Avatar too large (max 2MB)"


@pytest.mark.asyncio
async def test_change_avatar_invalid_extension_post(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test that an avatar file with an invalid extension returns HTTP 400."""
    test_user, user_token = await add_token(1000, 1000, test_db)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}

    response = test_setup.patch(
        f"{settings.API_V1_STR}/user/avatar",
        headers=headers,
        files={"avatar": ("invalid_file.txt", BytesIO(b"fake content"), "text/plain")},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Only PNG/JPG allowed"
