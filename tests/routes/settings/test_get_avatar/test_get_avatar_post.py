"""Test for get avatar endpoint via direct get call."""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status
from pytest_mock import MockerFixture


from src.config.config import settings
from src.models.user import User
from tests.conftest import add_token


@pytest.mark.asyncio
async def test_successful_get_avatar_default(
    test_setup: TestClient,
    test_db: AsyncSession,
    mocker: MockerFixture,
) -> None:
    """Test successful get default avatar with valid token."""
    user, user_token = await add_token(1000, 1000, test_db)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}

    test_path = Path(__file__).parent.parent.parent.parent / "data"
    file_name = "test_default_copy"
    file_name_ext = file_name + ".png"
    full_path = test_path / file_name_ext

    mocker.patch.object(
        settings,
        "UPLOAD_FOLDER_AVATARS",
        str(test_path),
    )
    mocker.patch.object(
        User,
        "avatar_filename_default",
        return_value=file_name,
    )
    assert full_path.is_file(), "Test avatar image must exist"

    response = test_setup.get(
        f"{settings.API_V1_STR}/user/avatar",
        headers=headers,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "image/png"
    assert response.content == full_path.read_bytes()


@pytest.mark.asyncio
async def test_successful_get_avatar_regular(
    test_setup: TestClient,
    test_db: AsyncSession,
    mocker: MockerFixture,
) -> None:
    """Test successful get regular avatar with valid token."""
    user, user_token = await add_token(1000, 1000, test_db)
    user.default_avatar = False
    test_db.add(user)
    await test_db.commit()
    headers = {"Authorization": f"Bearer {user_token.access_token}"}

    test_path = Path(__file__).parent.parent.parent.parent / "data"
    file_name = "test_default_copy"
    file_name_ext = file_name + ".png"
    full_path = test_path / file_name_ext

    mocker.patch.object(
        settings,
        "UPLOAD_FOLDER_AVATARS",
        str(test_path),
    )
    mocker.patch.object(
        User,
        "avatar_filename",
        return_value=file_name,
    )
    assert full_path.is_file(), "Test avatar image must exist"

    response = test_setup.get(
        f"{settings.API_V1_STR}/user/avatar",
        headers=headers,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "image/png"
    assert response.content == full_path.read_bytes()


@pytest.mark.asyncio
async def test_get_avatar_file_not_found(
    test_setup: TestClient,
    test_db: AsyncSession,
    mocker: MockerFixture,
) -> None:
    """Test get avatar with non-existent file."""
    _, user_token = await add_token(1000, 1000, test_db)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}

    mocker.patch(
        "os.path.isfile",
        return_value=False,
    )

    response = test_setup.get(
        f"{settings.API_V1_STR}/user/avatar",
        headers=headers,
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "An error occurred"}
