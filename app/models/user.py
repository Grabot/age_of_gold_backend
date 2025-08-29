import secrets
import time
import uuid
from hashlib import sha512
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import jwt as pyjwt
from argon2 import PasswordHasher, exceptions
from sqlmodel import Field, Relationship, SQLModel

from app.config.config import settings

ph = PasswordHasher()

if TYPE_CHECKING:
    from app.models.user_token import UserToken


# TODO: Move to util? Or move hash_password to user?
def hash_email(email: str, pepper: str) -> str:
    normalized_email = email.lower().encode("utf-8")
    peppered_email = normalized_email + pepper.encode("utf-8")
    return sha512(peppered_email).hexdigest()


def create_salt() -> str:
    return secrets.token_hex(8)


def avatar_filename() -> str:
    return uuid.uuid4().hex


class User(SQLModel, table=True):  # type: ignore[call-arg, unused-ignore]
    """
    User
    """

    __tablename__ = "User"  # pyright: ignore[reportAssignmentType]
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(default=None, index=True, unique=True)
    email_hash: str
    password_hash: str
    salt: str
    origin: int

    tokens: List["UserToken"] = Relationship(back_populates="user")

    def verify_password(self, hashed_password: str, provided_password: str) -> bool:
        try:
            return ph.verify(hashed_password, provided_password)
        except exceptions.VerificationError:
            return False

    def generate_auth_token(self, expires_in: int = 1800) -> str:
        payload: Dict[str, Any] = {
            "id": self.id,
            "iss": settings.JWT_ISS,
            "aud": settings.JWT_AUD,
            "sub": settings.JWT_SUB,
            "exp": int(time.time()) + expires_in,
            "iat": int(time.time()),
        }
        return pyjwt.encode(
            payload,
            settings.jwk_pem,
            algorithm=settings.header["alg"],
            headers=settings.header,
        )

    def generate_refresh_token(self, expires_in: int = 345600) -> str:
        payload: Dict[str, Any] = {
            "user_name": self.username,
            "iss": settings.JWT_ISS,
            "aud": settings.JWT_AUD,
            "sub": settings.JWT_SUB,
            "exp": int(time.time()) + expires_in,
            "iat": int(time.time()),
        }
        return pyjwt.encode(
            payload,
            settings.jwk_pem,
            algorithm=settings.header["alg"],
            headers=settings.header,
        )

    @property
    def serialize(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
        }
