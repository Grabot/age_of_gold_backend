"""Test for change avatar endpoint via direct function call."""

from io import BytesIO
from pathlib import Path
from typing import Any, Tuple
from unittest.mock import MagicMock, Mock

import pytest
from fastapi import HTTPException, UploadFile
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.api_v1.settings import change_avatar
from src.models.user import User
from src.models.user_token import UserToken
from tests.conftest import add_token


@pytest.mark.asyncio
async def test_successful_change_avatar_direct(
    test_setup: TestClient, test_db: AsyncSession, mocker: MockerFixture
) -> None:
    """Test successful change avatar via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    auth: Tuple[User, UserToken] = (test_user, test_user_token)
    test_user_id = test_user.id
    test_user.default_avatar = True
    test_db.add(test_user)
    await test_db.commit()

    test_path = Path(__file__).parent.parent.parent.parent.parent / "test_data"
    file_name = "test_default_copy"
    file_name_ext = file_name + ".png"
    full_path = test_path / file_name_ext
    assert full_path.is_file(), "Test avatar image must exist"

    with open(full_path, "rb") as f:
        file_content = f.read()
    file_like = BytesIO(file_content)
    avatar = UploadFile(
        filename=file_name_ext,
        file=file_like,
    )
    avatar.size = len(file_content)

    mocker.patch.object(User, "create_avatar", new_callable=Mock)

    request = MagicMock()
    request.app.state.s3.return_value = ""
    request.app.state.cipher.return_value = ""

    response_json: dict[str, Any] = await change_avatar.change_avatar(
        request, avatar, auth, test_db
    )

    assert response_json["success"]
    test_user_result = await test_db.get(User, test_user_id)
    assert test_user_result is not None
    assert test_user_result.default_avatar is False


@pytest.mark.asyncio
async def test_successful_change_avatar_default_direct(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test successful change avatar back to default via direct HTTP call."""
    test_user, user_token = await add_token(1000, 1000, test_db)
    auth: Tuple[User, UserToken] = (test_user, user_token)
    test_user_id = test_user.id
    test_user.default_avatar = False
    test_db.add(test_user)
    await test_db.commit()

    request = MagicMock()
    request.app.state.s3.return_value = ""
    request.app.state.cipher.return_value = ""

    response_json: dict[str, Any] = await change_avatar.change_avatar(
        request, None, auth, test_db
    )

    assert response_json["success"]
    test_user_result = await test_db.get(User, test_user_id)
    assert test_user_result is not None
    assert test_user_result.default_avatar


@pytest.mark.asyncio
async def test_change_avatar_invalid_file_direct(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test that an invalid avatar file raises HTTPException."""
    test_user, user_token = await add_token(1000, 1000, test_db)
    auth: Tuple[User, UserToken] = (test_user, user_token)

    avatar = UploadFile(filename="", file=BytesIO(b"fake content"))
    avatar.size = 0

    request = MagicMock()
    request.app.state.s3.return_value = ""
    request.app.state.cipher.return_value = ""

    with pytest.raises(HTTPException) as exc_info:
        await change_avatar.change_avatar(request, avatar, auth, test_db)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid avatar file"


@pytest.mark.asyncio
async def test_change_avatar_too_large_direct(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test that an avatar file that is too large raises HTTPException."""
    test_user, user_token = await add_token(1000, 1000, test_db)
    auth: Tuple[User, UserToken] = (test_user, user_token)

    avatar = UploadFile(
        filename="large_file.png", file=BytesIO(b"x" * (2 * 1024 * 1024 + 1))
    )
    avatar.size = 2 * 1024 * 1024 + 1

    request = MagicMock()
    request.app.state.s3.return_value = ""
    request.app.state.cipher.return_value = ""

    with pytest.raises(HTTPException) as exc_info:
        await change_avatar.change_avatar(request, avatar, auth, test_db)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Avatar too large (max 2MB)"


@pytest.mark.asyncio
async def test_change_avatar_invalid_extension_direct(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test that an avatar file with an invalid extension raises HTTPException."""
    test_user, user_token = await add_token(1000, 1000, test_db)
    auth: Tuple[User, UserToken] = (test_user, user_token)

    # Create an UploadFile with an invalid extension
    avatar = UploadFile(filename="invalid_file.txt", file=BytesIO(b"fake content"))
    avatar.size = 1024  # Valid size

    request = MagicMock()
    request.app.state.s3.return_value = ""
    request.app.state.cipher.return_value = ""

    with pytest.raises(HTTPException) as exc_info:
        await change_avatar.change_avatar(request, avatar, auth, test_db)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Only PNG/JPG allowed"
