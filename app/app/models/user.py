import base64
import os
import secrets
import time
from datetime import datetime, timedelta
from hashlib import md5
from typing import List, Optional

from authlib.jose import jwt
from passlib.apps import custom_app_context as pwd_context
from sqlalchemy import Index
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Field, Relationship, SQLModel, select

from app.config.config import settings
from app.models import Friend
import pytz


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
    about_me: Optional[str] = Field(default=None)
    origin: int
    # We set a default value with the timezone UTC, but than remove the timezone indicator with tzinfo=None to match the database
    tile_lock: datetime = Field(default=datetime.now(pytz.utc).replace(tzinfo=None))
    email_verified: bool = Field(default=False)
    default_avatar: bool = Field(default=True)
    is_admin: bool = Field(default=False)

    tokens: List["UserToken"] = Relationship(back_populates="user")

    friends: List["Friend"] = Relationship(
        back_populates="friend",
        sa_relationship_kwargs={
            "primaryjoin": "User.id==Friend.user_id",
        },
    )
    followers: List["Friend"] = Relationship(
        back_populates="follower",
        sa_relationship_kwargs={
            "primaryjoin": "User.id==Friend.friend_id",
        },
    )

    guild: Optional["Guild"] = Relationship(
        back_populates="guild_member",
        sa_relationship_kwargs={
            "uselist": False,
            "primaryjoin": "and_(User.id==Guild.user_id, Guild.accepted==True)",
        },
    )

    tiles_changed: List["Tile"] = Relationship(
        back_populates="user_changed",
    )

    __table_args__ = (Index("user_index", "email_hash", "origin", unique=True),)

    def get_tile_lock(self):
        return self.tile_lock

    def lock_tile_setting(self, minutes):
        self.tile_lock = datetime.now(pytz.utc).replace(tzinfo=None) + timedelta(minutes=minutes)

    def can_change_tile_type(self):
        return self.tile_lock <= datetime.now(pytz.utc).replace(tzinfo=None)

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

    def befriend(self, user):
        # Only call if the Friend object is not present yet.
        friend = Friend(user_id=self.id, friend_id=user.id, friend_name=user.username)
        return friend

    async def is_friend(self, db: AsyncSession, user):
        if user:
            friend_statement = select(Friend).filter_by(user_id=self.id, friend_id=user.id)
            results = await db.execute(friend_statement)
            friend = results.first()
            if friend:
                return friend.Friend.accepted
            else:
                return False
        else:
            return False

    def generate_auth_token(self, expires_in=1800):
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

    def generate_refresh_token(self, expires_in=345600):
        payload = {
            "user_name": self.username,
            "iss": settings.JWT_ISS,
            "aud": settings.JWT_AUD,
            "sub": settings.JWT_SUB,
            "exp": int(time.time()) + expires_in,  # expiration time
            "iat": int(time.time()),  # issued at
        }
        return jwt.encode(settings.header, payload, settings.jwk)

    def is_verified(self):
        return self.email_verified

    def verify_user(self):
        self.email_verified = True

    def avatar_filename(self):
        return md5(self.email_hash.encode("utf-8")).hexdigest()

    def avatar_filename_small(self):
        return self.avatar_filename() + "_small"

    def avatar_filename_default(self):
        return self.avatar_filename() + "_default"

    def set_new_username(self, new_username):
        self.username = new_username

    def set_default_avatar(self, value):
        self.default_avatar = value

    def is_default(self):
        return self.default_avatar

    def get_user_avatar(self, full=False):
        if self.default_avatar:
            file_name = self.avatar_filename_default()
        else:
            if full:
                file_name = self.avatar_filename()
            else:
                file_name = self.avatar_filename_small()
        file_folder = settings.UPLOAD_FOLDER_AVATARS

        file_path = os.path.join(file_folder, "%s.png" % file_name)
        if not os.path.isfile(file_path):
            return None
        else:
            with open(file_path, "rb") as fd:
                image_as_base64 = base64.encodebytes(fd.read()).decode()
            return image_as_base64

    def get_friend_ids(self):
        return [friend.serialize_minimal for friend in self.friends]

    @property
    def serialize(self):
        # Get detailed user information, mostly used for login
        return {
            "id": self.id,
            "username": self.username,
            "verified": self.email_verified,
            "tile_lock": self.tile_lock.strftime("%Y-%m-%dT%H:%M:%S.%f"),
            "friends": self.get_friend_ids(),
            "avatar": self.get_user_avatar(True),
            "guild": self.guild.serialize if self.guild else None,
            "origin": self.origin == 0, # we only want to know if it's a regular login
            "is_admin": self.is_admin,
        }

    @property
    def serialize_get(self):
        # get user details without personal information
        return {
            "id": self.id,
            "username": self.username,
            "avatar": self.get_user_avatar(True),
        }

    @property
    def serialize_minimal(self):
        # get minimal user details
        return {
            "id": self.id,
            "username": self.username,
            "avatar": self.get_user_avatar(False),
        }

    @property
    def serialize_no_detail(self):
        return {
            "id": self.id,
            "username": self.username,
            "origin": self.origin == 0,
        }
