"""Test for logout endpoint via direct function call."""

from io import BytesIO
from typing import Tuple
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncSession
from botocore.exceptions import ClientError

from src.api.api_v1.settings import get_avatar
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

    request = MagicMock()
    request.app.state.s3.return_value = ""
    request.app.state.cipher.return_value = ""

    response_file: StreamingResponse = await get_avatar.get_avatar(
        request, True, auth, test_db
    )

    assert response_file.status_code == status.HTTP_200_OK
    assert response_file.headers["content-type"] == "image/png"


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

    request = MagicMock()
    request.app.state.s3 = MagicMock()
    request.app.state.cipher = MagicMock()

    fake_encrypted_data = b"fake_encrypted_data"

    def mock_download_fileobj(bucket: str, key: str, buffer: BytesIO) -> None:
        buffer.write(fake_encrypted_data)
        buffer.seek(0)

    request.app.state.s3.download_fileobj = mock_download_fileobj

    fake_decrypted_data = b"fake_decrypted_data"
    request.app.state.cipher.decrypt.return_value = fake_decrypted_data

    response_file: StreamingResponse = await get_avatar.get_avatar(
        request, False, auth, test_db
    )

    assert response_file.status_code == status.HTTP_200_OK
    assert response_file.headers["content-type"] == "image/png"

    body = b"".join(
        [
            chunk
            async for chunk in response_file.body_iterator
            if isinstance(chunk, bytes)
        ]
    )
    assert body == fake_decrypted_data


@pytest.mark.asyncio
async def test_get_avatar_file_not_found_direct(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test get avatar with non-existent file via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    request = MagicMock()
    request.app.state.s3 = MagicMock()
    request.app.state.cipher = MagicMock()

    # Mock s3_client.download_fileobj to raise a ClientError with NoSuchKey
    error_response = {
        "Error": {"Code": "NoSuchKey", "Message": "The specified key does not exist."}
    }
    request.app.state.s3.download_fileobj.side_effect = ClientError(
        error_response, "GetObject"
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_avatar.get_avatar(request, True, auth, test_db)

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "Avatar not found"


@pytest.mark.asyncio
async def test_get_avatar_internal_error_direct(
    test_setup: TestClient,
    test_db: AsyncSession,
) -> None:
    """Test get avatar with an internal S3 error (500) via direct function call."""
    test_user, test_user_token = await add_token(1000, 1000, test_db)
    auth: Tuple[User, UserToken] = (test_user, test_user_token)

    request = MagicMock()
    request.app.state.s3 = MagicMock()
    request.app.state.cipher = MagicMock()

    error_response = {
        "Error": {
            "Code": "InternalError",  # Any error code other than "NoSuchKey"
            "Message": "Something went wrong on S3.",
        }
    }
    request.app.state.s3.download_fileobj.side_effect = ClientError(
        error_response, "GetObject"
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_avatar.get_avatar(request, True, auth, test_db)

    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert exc_info.value.detail == "Failed to fetch avatar"
