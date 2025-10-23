"""Test file for user model."""

# ruff: noqa: E402
import sys
from pathlib import Path

import pytest
import jwt as pyjwt

current_dir = Path(__file__).parent
sys.path.append(str(current_dir.parent.parent))

from src.models import User  # pylint: disable=C0413
from src.config.config import settings  # pylint: disable=C0413
from src.models.user import avatar_filename, create_salt, hash_email  # pylint: disable=C0413
from src.util.util import hash_password  # pylint: disable=C0413


def test_hash_email() -> None:
    """Test that the hash_email function returns a string of length 128"""
    email = "test@example.com"
    pepper = "pepper"
    expected_hash = hash_email(email, pepper)
    assert isinstance(expected_hash, str)
    assert len(expected_hash) == 128


def test_create_salt() -> None:
    """Test that the create_salt function returns a string of length 16"""
    salt = create_salt()
    assert isinstance(salt, str)
    assert len(salt) == 16


def test_avatar_filename() -> None:
    """Test that the avatar_filename function returns a string of length 32"""
    filename = avatar_filename()
    assert isinstance(filename, str)
    assert len(filename) == 32


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
    )
    token = user.generate_auth_token()
    assert isinstance(token, str)
    assert len(token) > 0
    try:
        decoded_token = pyjwt.decode(
            token,
            settings.jwt_pem,
            algorithms=[settings.header["alg"]],
            options={"verify_aud": False},
        )
    except Exception as exc:
        raise AssertionError("token decoding failed") from exc
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
    )
    token = user.generate_refresh_token()
    assert isinstance(token, str)
    assert len(token) > 0
    try:
        decoded_token = pyjwt.decode(
            token,
            settings.jwt_pem,
            algorithms=[settings.header["alg"]],
            options={"verify_aud": False},
        )
    except Exception as exc:
        raise AssertionError("token decoding failed") from exc
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
    )
    serialized_user = user.serialize
    assert isinstance(serialized_user, dict)
    assert serialized_user["id"] == 1
    assert serialized_user["username"] == "testuser"


if __name__ == "__main__":
    pytest.main([__file__])
