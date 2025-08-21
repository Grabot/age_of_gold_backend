
import secrets
import time

from typing import Optional, List

from authlib.jose import jwt
from passlib.apps import custom_app_context as pwd_context

from app.config.config import settings
from sqlmodel import SQLModel, Field, Relationship


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

    def hash_password(self, password):
        salt = secrets.token_hex(8)
        self.salt = salt
        self.password_hash = pwd_context.hash(password + salt)

    def verify_password(self, password):
        # If the user has any other origin than regular it should not get here
        # because the verification is does elsewhere. So if it does, we return False
        if self.origin != 0:
            return False
        else:
            return pwd_context.verify(password + self.salt, self.password_hash)

    def generate_auth_token(self, expires_in=1800):
        payload = {
            "id": self.id,
            "iss": settings.JWT_ISS,
            "aud": settings.JWT_AUD,
            "sub": settings.JWT_SUB,
            "exp": int(time.time()) + expires_in,
            "iat": int(time.time()),
        }
        return jwt.encode(settings.header, payload, settings.jwk)

    def generate_refresh_token(self, expires_in=345600):
        payload = {
            "user_name": self.username,
            "iss": settings.JWT_ISS,
            "aud": settings.JWT_AUD,
            "sub": settings.JWT_SUB,
            "exp": int(time.time()) + expires_in,
            "iat": int(time.time()),
        }
        return jwt.encode(settings.header, payload, settings.jwk)

    @property
    def serialize(self):
        return {
            "id": self.id,
            "username": self.username,
        }
