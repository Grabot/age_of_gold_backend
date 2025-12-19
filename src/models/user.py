"""User model"""

import os
import secrets
import time
import uuid
from hashlib import md5, sha512
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

import jwt as pyjwt
from argon2 import PasswordHasher, exceptions
from sqlmodel import Field, Relationship, SQLModel

from src.config.config import settings
from src.config.jwt_key import jwt_private_key

ph = PasswordHasher()

if TYPE_CHECKING:
    from src.models.user_token import UserToken


def hash_email(email: str) -> str:
    """Hash the email address with a pepper."""
    normalized_email = email.lower().encode("utf-8")
    peppered_email = normalized_email + settings.PEPPER.encode("utf-8")
    return sha512(peppered_email).hexdigest()


def create_salt() -> str:
    """Create a random salt for password hashing."""
    return secrets.token_hex(8)


class User(SQLModel, table=True):  # type: ignore[call-arg, unused-ignore]
    """
    User model representing a user in the system.
    """

    __tablename__ = "User"  # pyright: ignore[reportAssignmentType]
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(default=None, index=True, unique=True)
    email_hash: str
    password_hash: str
    salt: str
    origin: int
    default_avatar: bool = Field(default=True)
    profile_version: int = Field(default=1)
    avatar_version: int = Field(default=1)

    tokens: List["UserToken"] = Relationship(back_populates="user")

    def avatar_filename(self) -> str:
        """get the name of the avatar file for this user."""
        return md5(self.email_hash.encode("utf-8")).hexdigest()

    def avatar_filename_default(self) -> str:
        """get the name of the default avatar file for this user."""
        return self.avatar_filename() + "_default"

    def verify_password(self, hashed_password: str, provided_password: str) -> bool:
        """Verify the provided password against the stored hash."""
        try:
            return ph.verify(hashed_password, provided_password)
        except exceptions.VerificationError:
            return False

    def create_avatar(self, avatar_bytes: bytes) -> None:
        """Create an avatar for the user."""
        file_folder = settings.UPLOAD_FOLDER_AVATARS
        file_name = self.avatar_filename() + ".png"

        file_path = os.path.join(file_folder, file_name)
        with open(file_path, "wb") as f:
            f.write(avatar_bytes)

    def remove_avatar(self) -> None:
        """Remove the avatar for the user."""
        file_folder = settings.UPLOAD_FOLDER_AVATARS
        file_name = self.avatar_filename() + ".png"

        if os.path.exists(os.path.join(file_folder, file_name)):
            os.remove(os.path.join(file_folder, file_name))

    def remove_avatar_default(self) -> None:
        """Remove the default avatar for the user."""
        file_folder = settings.UPLOAD_FOLDER_AVATARS
        file_name = self.avatar_filename_default() + ".png"

        if os.path.exists(os.path.join(file_folder, file_name)):
            os.remove(os.path.join(file_folder, file_name))

    def generate_auth_token(
        self, expires_in: int = 1800, scopes: Optional[List[str]] = None
    ) -> str:
        """Generate an authentication token for the user."""
        payload: Dict[str, Any] = {
            "sub": str(self.id),
            "iss": settings.JWT_ISS,
            "aud": settings.JWT_AUD,
            "jti": str(uuid.uuid4()),
            "typ": "access",
            "exp": int(time.time()) + expires_in,
            "iat": int(time.time()),
        }
        if scopes:
            payload["scope"] = " ".join(scopes)
        return pyjwt.encode(
            payload,
            jwt_private_key,
            algorithm=settings.header["alg"],
            headers=settings.header,
        )

    def generate_refresh_token(
        self,
        expires_in: int = 345600,
    ) -> str:
        """Generate a refresh token for the user."""
        payload: Dict[str, Any] = {
            "sub": str(self.id),
            "iss": settings.JWT_ISS,
            "aud": settings.JWT_AUD,
            "jti": str(uuid.uuid4()),
            "typ": "refresh",
            "exp": int(time.time()) + expires_in,
        }
        return pyjwt.encode(
            payload,
            jwt_private_key,
            algorithm=settings.header["alg"],
            headers=settings.header,
        )

    @property
    def serialize(self) -> Dict[str, Union[Optional[int], str]]:
        """Serialize the user object to a dictionary."""
        return {
            "id": self.id,
            "username": self.username,
        }
