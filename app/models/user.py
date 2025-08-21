import secrets
import time
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from authlib.jose import jwt
from passlib.apps import custom_app_context as pwd_context
from sqlmodel import Field, Relationship, SQLModel

from app.config.config import settings

if TYPE_CHECKING:
    from app.models.user_token import UserToken


class User(SQLModel, table=True):
    """
    User
    """

    __tablename__ = "User"
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(default=None, index=True, unique=True)
    email_hash: str
    password_hash: str
    salt: str
    origin: int

    tokens: List["UserToken"] = Relationship(back_populates="user")

    def hash_password(self, password: str) -> None:
        salt = secrets.token_hex(8)
        self.salt = salt
        self.password_hash = pwd_context.hash(password + salt)

    def verify_password(self, password: str) -> bool:
        if self.origin != 0:
            return False
        else:
            return pwd_context.verify(password + self.salt, self.password_hash)

    def generate_auth_token(self, expires_in: int = 1800) -> bytes:
        payload: Dict[str, Any] = {
            "id": self.id,
            "iss": settings.JWT_ISS,
            "aud": settings.JWT_AUD,
            "sub": settings.JWT_SUB,
            "exp": int(time.time()) + expires_in,
            "iat": int(time.time()),
        }
        return jwt.encode(settings.header, payload, settings.jwk)  # type: ignore

    def generate_refresh_token(self, expires_in: int = 345600) -> bytes:
        payload: Dict[str, Any] = {
            "user_name": self.username,
            "iss": settings.JWT_ISS,
            "aud": settings.JWT_AUD,
            "sub": settings.JWT_SUB,
            "exp": int(time.time()) + expires_in,
            "iat": int(time.time()),
        }
        return jwt.encode(settings.header, payload, settings.jwk)  # type: ignore

    @property
    def serialize(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
        }
