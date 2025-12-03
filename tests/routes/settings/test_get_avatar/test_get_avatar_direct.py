"""Test for logout endpoint via direct function call."""

from pathlib import Path
from typing import Tuple

import pytest
from fastapi import HTTPException, status
from fastapi.responses import FileResponse
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.settings import get_avatar
from src.config.config import settings
from src.models.user import User
from src.models.user_token import UserToken
from tests.conftest import add_token


@pytest.mark.asyncio
async def test_successful_get_avatar_default_direct(
    test_setup: TestClient, test_db: AsyncSession, mocker: MockerFixture
) -> None:
    """Test successful get default avatar via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    auth: Tuple[User, UserToken] = (test_user, test_user_token)
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

    response_file: FileResponse = await get_avatar.get_avatar(True, auth, test_db)

    assert response_file.status_code == status.HTTP_200_OK
    assert response_file.headers["content-type"] == "image/png"
    response_path = Path(response_file.path)
    assert response_path == full_path


@pytest.mark.asyncio
async def test_successful_get_avatar_regular_direct(
    test_setup: TestClient, test_db: AsyncSession, mocker: MockerFixture
) -> None:
    """Test successful get regular avatar via direct function call."""
    user, test_user_token = await add_token(1000, 1000, test_db)
    user.default_avatar = False
    test_db.add(user)
    await test_db.commit()
    auth: Tuple[User, UserToken] = (user, test_user_token)
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

    response_file: FileResponse = await get_avatar.get_avatar(False, auth, test_db)

    assert response_file.status_code == status.HTTP_200_OK
    assert response_file.headers["content-type"] == "image/png"
    response_path = Path(response_file.path)
    assert response_path == full_path


@pytest.mark.asyncio
async def test_get_avatar_file_not_found_direct(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test get avatar with non-existent file via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    # Expect an HTTPException to be raised
    with pytest.raises(HTTPException) as exc_info:
        await get_avatar.get_avatar(True, auth, test_db)

    # Assert the exception details
    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert exc_info.value.detail == "An error occurred"
