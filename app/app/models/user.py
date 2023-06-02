import time
from datetime import datetime
from typing import Optional

from authlib.jose import jwt
from config import settings
from passlib.apps import custom_app_context as pwd_context
from sqlalchemy import Index
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """
    User
    """

    __tablename__ = "User"
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(default=None, index=True, unique=True)
    email: str
    password_hash: str
    about_me: Optional[str] = Field(default=None)
    last_seen: datetime = Field(default=datetime.utcnow())
    origin: int
    token: Optional[str] = Field(default=None, index=True)
    token_expiration: Optional[int] = Field(default=None)
    tile_lock: datetime = Field(default=datetime.utcnow())
    email_verified: bool = Field(default=False)
    default_avatar: bool = Field(default=True)

    # friends: List["Friend"] = Relationship(back_populates="user")
    # followers: List["Friend"] = Relationship()

    __table_args__ = (Index("user_index", "email", "origin", unique=True),)

    def hash_password(self, password):
        self.password_hash = pwd_context.hash(password)

    def generate_auth_token(self, expires_in=3600):
        # also used for email password reset token
        payload = {
            "id": self.id,
            "iss": settings.JWT_ISS,
            "aud": settings.JWT_AUD,
            "sub": settings.JWT_SUB,
            "exp": int(time.time()) + expires_in,  # expiration time
            "iat": int(time.time()),  # issued at
        }
        return jwt.encode(settings.header, payload, settings.jwk)

    def generate_refresh_token(self, expires_in=36000):
        payload = {
            "user_name": self.username,
            "iss": settings.JWT_ISS,
            "aud": settings.JWT_AUD,
            "sub": settings.JWT_SUB,
            "exp": int(time.time()) + expires_in,  # expiration time
            "iat": int(time.time()),  # issued at
        }
        return jwt.encode(settings.header, payload, settings.jwk)

    def set_token(self, token):
        self.token = token

    def set_token_expiration(self, token_expiration):
        self.token_expiration = token_expiration

    @property
    def serialize(self):
        # Get detailed user information, mostly used for login
        return {
            "id": self.id,
            "username": self.username,
            "verified": self.email_verified,
            "tile_lock": self.tile_lock.strftime("%Y-%m-%dT%H:%M:%S.%f"),
        }
