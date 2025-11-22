"""Test file for user model."""

from pathlib import Path
import jwt as pyjwt
from pytest_mock import MockerFixture
from src.config.config import settings
from src.models import User
from src.models.user import create_salt, hash_email
from src.util.util import hash_password


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
    token = user.generate_auth_token(expires_in=180, scopes=["user"])
    assert isinstance(token, str)
    assert len(token) > 0
    decoded_token = pyjwt.decode(
        token,
        settings.jwt_pem,
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
    )
    token = user.generate_refresh_token()
    assert isinstance(token, str)
    assert len(token) > 0
    decoded_token = pyjwt.decode(
        token,
        settings.jwt_pem,
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
    )
    serialized_user = user.serialize
    assert isinstance(serialized_user, dict)
    assert serialized_user["id"] == 1
    assert serialized_user["username"] == "testuser"


def test_user_create_avatar(
    mocker: MockerFixture,
) -> None:
    """Test that create_avatar writes the avatar file correctly."""
    test_user = User(
        username="testuser",
        email_hash="test@example.com",
        password_hash="hashedpassword",
        salt="salt",
        origin=0,
    )

    test_image_path = Path(__file__).parent.parent / "data" / "test_default_copy.png"
    assert test_image_path.is_file(), "Test image must exist"

    test_image_bytes = test_image_path.read_bytes()

    temp_upload_folder = Path(__file__).parent / "temp_avatars"
    temp_upload_folder.mkdir(exist_ok=True)

    mocker.patch.object(settings, "UPLOAD_FOLDER_AVATARS", str(temp_upload_folder))

    test_user.create_avatar(test_image_bytes)

    expected_filename = test_user.avatar_filename() + ".png"
    expected_path = temp_upload_folder / expected_filename

    assert expected_path.is_file(), "Avatar file was not created"

    created_content = expected_path.read_bytes()
    assert created_content == test_image_bytes, "Avatar file content does not match"

    test_user.remove_avatar()
    assert not expected_path.is_file(), "Avatar file was not removed"

    # Test remove with no file
    test_user.remove_avatar()
    assert not expected_path.is_file(), "Avatar file was not removed"

    temp_upload_folder.rmdir()
