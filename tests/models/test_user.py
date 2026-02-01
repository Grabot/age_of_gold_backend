"""Test file for user model."""

from pathlib import Path
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError

import jwt as pyjwt

from src.config.config import settings
from src.config.jwt_key import jwt_public_key
from src.models import User
from src.models.user import create_salt, hash_email
from src.util.util import get_random_colour, hash_password


def test_hash_email() -> None:
    """Test that the hash_email function returns a string of length 128"""
    email = "test@example.com"
    expected_hash = hash_email(email)
    assert isinstance(expected_hash, str)
    assert len(expected_hash) == 128


def test_create_salt() -> None:
    """Test that the create_salt function returns a string of length 16"""
    salt = create_salt()
    assert isinstance(salt, str)
    assert len(salt) == 16


def test_user_verify_password() -> None:
    """Test that the verify_password method correctly verifies passwords"""
    password = "testpassword"
    salt = "salt"
    password_with_salt = password + salt
    password_hash = hash_password(password=password_with_salt)
    user = User(
        id=1,
        username="testuser",
        origin=0,
        email_hash="not_important",
        password_hash=password_hash,
        salt=salt,
        colour=get_random_colour()
    )
    assert user.verify_password(password_hash, password_with_salt) is True
    assert user.verify_password(password_hash, "wrongpassword") is False


def test_user_generate_auth_token() -> None:
    """Test that the generate_auth_token method returns a valid JWT token"""
    user = User(
        id=123,
        username="testuser",
        origin=0,
        email_hash="not_important",
        password_hash="not_important",
        salt="not_important",
        colour=get_random_colour()
    )
    token = user.generate_auth_token(expires_in=180, scopes=["user"])
    assert isinstance(token, str)
    assert len(token) > 0
    decoded_token = pyjwt.decode(
        token,
        jwt_public_key,
        algorithms=[settings.header["alg"]],
        options={"verify_aud": False},
    )
    assert "sub" in decoded_token
    assert decoded_token["sub"] == "123"


def test_user_generate_refresh_token() -> None:
    """Test that the generate_refresh_token method returns a valid JWT token"""
    user = User(
        id=123,
        username="testuser",
        origin=0,
        email_hash="not_important",
        password_hash="not_important",
        salt="not_important",
        colour=get_random_colour()
    )
    token = user.generate_refresh_token()
    assert isinstance(token, str)
    assert len(token) > 0
    decoded_token = pyjwt.decode(
        token,
        jwt_public_key,
        algorithms=[settings.header["alg"]],
        options={"verify_aud": False},
    )
    assert "sub" in decoded_token
    assert decoded_token["sub"] == "123"


def test_user_serialize() -> None:
    """Test that the serialize property returns a dictionary with the correct user data"""
    user = User(
        id=1,
        username="testuser",
        origin=0,
        email_hash="not_important",
        password_hash="not_important",
        salt="not_important",
        colour=get_random_colour()
    )
    serialized_user = user.serialize
    assert isinstance(serialized_user, dict)
    assert serialized_user["id"] == 1
    assert serialized_user["username"] == "testuser"


def test_user_create_avatar() -> None:
    """Test that create_avatar writes the avatar file correctly."""
    test_user = User(
        username="testuser",
        email_hash="test@example.com",
        password_hash="hashedpassword",
        salt="salt",
        origin=0,
        colour=get_random_colour()
    )

    mock_cipher = MagicMock()
    mock_s3_client = MagicMock()

    test_image_path = (
        Path(__file__).parent.parent.parent / "test_data" / "test_default_copy.png"
    )
    assert test_image_path.is_file(), "Test image must exist"

    test_image_bytes = test_image_path.read_bytes()
    mock_cipher.encrypt.return_value = test_image_bytes
    mock_s3_client.upload_fileobj = MagicMock()

    temp_upload_folder = Path(__file__).parent / "temp_avatars"
    temp_upload_folder.mkdir(exist_ok=True)

    test_user.create_avatar(mock_s3_client, mock_cipher, test_image_bytes)

    mock_cipher.encrypt.assert_called_once_with(test_image_bytes)
    mock_s3_client.upload_fileobj.assert_called_once()

    args, kwargs = mock_s3_client.upload_fileobj.call_args
    buffer, _, _ = args
    extra_args = kwargs.get("ExtraArgs", {})

    buffer.seek(0)
    buffer_content = buffer.read()
    assert buffer_content == test_image_bytes, (
        "Buffer content should match encrypted data"
    )

    assert extra_args.get("ContentType") == "application/octet-stream"


def test_delete_default_avatar() -> None:
    """Test that the default avatar deletion function works."""
    test_user = User(
        username="testuser",
        email_hash="test@example.com",
        password_hash="hashedpassword",
        salt="salt",
        origin=0,
        colour=get_random_colour()
    )

    mock_s3_client = MagicMock()
    mock_s3_client.delete_object = MagicMock()

    test_user.remove_avatar_default(mock_s3_client)


def test_remove_avatar_logs_error_on_client_error() -> None:
    """Test that remove_avatar logs an error on S3 ClientError."""
    test_user = User(
        username="testuser",
        email_hash="test@example.com",
        password_hash="hashedpassword",
        salt="salt",
        origin=0,
        colour=get_random_colour()
    )

    mock_s3_client = MagicMock()
    mock_s3_client.delete_object.side_effect = ClientError(
        {"Error": {"Code": "NoSuchKey", "Message": "The object does not exist."}},
        "DeleteObject",
    )

    with patch("src.models.user.logger.error") as mock_logger:
        test_user.remove_avatar(mock_s3_client)

        mock_logger.assert_called_once()
        assert "failed to remove avatar:" in mock_logger.call_args[0][0]


def test_remove_avatar_default_logs_error_on_client_error() -> None:
    """Test that remove_avatar_default logs an error on S3 ClientError."""
    test_user = User(
        username="testuser",
        email_hash="test@example.com",
        password_hash="hashedpassword",
        salt="salt",
        origin=0,
        colour=get_random_colour()
    )

    mock_s3_client = MagicMock()
    mock_s3_client.delete_object.side_effect = ClientError(
        {"Error": {"Code": "NoSuchKey", "Message": "The object does not exist."}},
        "DeleteObject",
    )

    with patch("src.models.user.logger.error") as mock_logger:
        test_user.remove_avatar_default(mock_s3_client)

        mock_logger.assert_called_once()
        assert "failed to remove avatar:" in mock_logger.call_args[0][0]
