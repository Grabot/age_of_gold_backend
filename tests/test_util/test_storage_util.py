"""Test file for storage util"""

import pytest
from unittest.mock import MagicMock
from io import BytesIO
from cryptography.fernet import Fernet
from PIL import Image
import numpy as np

from src.util.storage_util import (
    download_image,
    upload_image,
    decrypt_image,
)


@pytest.fixture(name="s3_mock")
def mock_s3_client() -> MagicMock:
    """Fixture for a mocked S3 client."""
    return MagicMock()


@pytest.fixture(name="cipher_mock")
def cipher() -> Fernet:
    """Fixture for a Fernet cipher."""
    return Fernet(Fernet.generate_key())


@pytest.fixture(name="image_mock")
def test_image() -> Image.Image:
    """Fixture for a test PIL image."""
    return Image.fromarray(np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8))


@pytest.fixture(name="image_bytes_mock")
def test_image_bytes(image_mock: Image.Image) -> bytes:
    """Fixture for test image bytes."""
    buffer = BytesIO()
    image_mock.save(buffer, format="PNG")
    return buffer.getvalue()


def test_decrypt_image(image_bytes_mock: bytes, cipher_mock: Fernet) -> None:
    """Test that decrypt_image returns decrypted bytes."""
    encrypted_data: bytes = cipher_mock.encrypt(image_bytes_mock)
    decrypted_data: bytes = decrypt_image(encrypted_data, cipher_mock)
    assert decrypted_data == image_bytes_mock


def test_upload_image(
    s3_mock: MagicMock, cipher_mock: Fernet, image_bytes_mock: bytes
) -> None:
    """Test that upload_image calls S3 upload_fileobj with encrypted data."""
    buffer: BytesIO = BytesIO()
    encrypted_data: bytes = cipher_mock.encrypt(image_bytes_mock)
    buffer.write(encrypted_data)
    buffer.seek(0)

    upload_image(s3_mock, cipher_mock, image_bytes_mock, "test-bucket", "test-key")

    s3_mock.upload_fileobj.assert_called_once()
    args, kwargs = s3_mock.upload_fileobj.call_args
    assert args[1] == "test-bucket"
    assert args[2] == "test-key"
    assert kwargs["ExtraArgs"]["ContentType"] == "application/octet-stream"


def test_download_image_encrypted(
    s3_mock: MagicMock, cipher_mock: Fernet, image_bytes_mock: bytes
) -> None:
    """Test that download_image returns decrypted data when encrypted=True."""
    s3_mock.download_fileobj.side_effect = lambda bucket, key, buffer: buffer.write(
        cipher_mock.encrypt(image_bytes_mock)
    )

    result = download_image(
        s3_mock, cipher_mock, "test-bucket", "test-key", encrypted=True
    )
    assert result == image_bytes_mock


def test_download_image_not_encrypted(
    s3_mock: MagicMock, cipher_mock: Fernet, image_bytes_mock: bytes
) -> None:
    """Test that download_image returns raw data when encrypted=False."""
    s3_mock.download_fileobj.side_effect = lambda bucket, key, buffer: buffer.write(
        image_bytes_mock
    )

    result = download_image(
        s3_mock, cipher_mock, "test-bucket", "test-key", encrypted=False
    )
    assert result == image_bytes_mock


def test_decrypt_image_invalid_data(cipher_mock: Fernet) -> None:
    """Test that decrypt_image raises an exception for invalid data."""
    with pytest.raises(Exception):
        decrypt_image(b"invalid_data", cipher_mock)


def test_upload_image_empty_data(s3_mock: MagicMock, cipher_mock: Fernet) -> None:
    """Test that upload_image handles empty data."""
    upload_image(s3_mock, cipher_mock, b"", "test-bucket", "test-key")
    s3_mock.upload_fileobj.assert_called_once()


def test_download_image_empty_data(s3_mock: MagicMock, cipher_mock: Fernet) -> None:
    """Test that download_image handles empty data."""
    s3_mock.download_fileobj.side_effect = lambda bucket, key, buffer: buffer.write(b"")

    result = download_image(
        s3_mock, cipher_mock, "test-bucket", "test-key", encrypted=False
    )
    assert result == b""
