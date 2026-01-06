"""Test for get avatar endpoint via direct get call."""

from io import BytesIO
import pytest
from unittest.mock import MagicMock
from fastapi import status
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import FastAPI
from typing import cast
from botocore.exceptions import ClientError
from src.config.config import settings
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

    response = test_setup.post(
        f"{settings.API_V1_STR}/user/avatar",
        headers=headers,
        json={
            "user_id": user.id,
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "image/png"


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

    mock_s3 = MagicMock()

    def mock_download_fileobj(bucket: str, key: str, buffer: BytesIO) -> None:
        buffer.write(b"mocked_encrypted_data")
        buffer.seek(0)

    mock_s3.download_fileobj.side_effect = mock_download_fileobj
    cast(FastAPI, test_setup.app).state.s3 = mock_s3

    mocker.patch(
        "src.util.storage_util.decrypt_image", return_value=b"mocked_decrypted_data"
    )

    response = test_setup.post(
        f"{settings.API_V1_STR}/user/avatar",
        headers=headers,
        json={
            "user_id": user.id,
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "image/png"


@pytest.mark.asyncio
async def test_get_avatar_file_not_found(
    test_setup: TestClient,
    test_db: AsyncSession,
    mocker: MockerFixture,
) -> None:
    """Test get avatar with non-existent file."""
    user, user_token = await add_token(1000, 1000, test_db)
    headers = {"Authorization": f"Bearer {user_token.access_token}"}

    mock_s3 = MagicMock()
    mock_s3.download_fileobj.side_effect = ClientError(
        {
            "Error": {
                "Code": "NoSuchKey",
                "Message": "The specified key does not exist.",
            }
        },
        "GetObject",
    )

    cast(FastAPI, test_setup.app).state.s3 = mock_s3

    response = test_setup.post(
        f"{settings.API_V1_STR}/user/avatar",
        headers=headers,
        json={
            "user_id": user.id,
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Avatar not found"}
