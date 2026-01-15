"""Chat model."""

import secrets
import time
import uuid
from hashlib import md5, sha512
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

import jwt as pyjwt
from argon2 import PasswordHasher, exceptions
from botocore.exceptions import ClientError
from cryptography.fernet import Fernet
from sqlmodel import ARRAY, Column, Field, Integer, Relationship, SQLModel

from src.config.config import settings
from src.config.jwt_key import jwt_private_key
from src.util.gold_logging import logger
from src.util.storage_util import upload_image

if TYPE_CHECKING:
    from src.models import Group


class Chat(SQLModel, table=True):
    """
    Chat
    """

    __tablename__ = "Chat"  # pyright: ignore[reportAssignmentType]
    id: int = Field(default=None, primary_key=True)
    user_ids: List[int] = Field(default=[], sa_column=Column(ARRAY(Integer())))
    user_admin_ids: List[int] = Field(default=[], sa_column=Column(ARRAY(Integer())))
    private: bool = Field(default=True)
    group_name: str
    group_description: str
    group_colour: str
    default_avatar: bool = Field(default=True)
    current_message_id: int
    last_message_read_id_chat: int = Field(default=1)

    groups: List["Group"] = Relationship(
        back_populates="chat",
        sa_relationship_kwargs={
            "uselist": True,
            "primaryjoin": "Chat.id==Group.group_id",
        },
    )

    def add_user(self, user_id: int) -> None:
        new_users = self.user_ids + [user_id]
        new_users.sort()
        self.user_ids = new_users

    def remove_user(self, user_id: int) -> None:
        self.user_ids = [
            current_user_id
            for current_user_id in self.user_ids
            if user_id != current_user_id
        ]

    def add_admin(self, user_id: int) -> None:
        new_admins = self.user_admin_ids + [user_id]
        new_admins.sort()
        self.user_admin_ids = new_admins

    def remove_admin(self, user_id: int) -> None:
        self.user_admin_ids = [
            admin_id for admin_id in self.user_admin_ids if admin_id != user_id
        ]


    def group_avatar_filename(self) -> str:
        """get the name of the group avatar file for this user."""
        return md5(str(self.id).encode("utf-8")).hexdigest()

    def group_avatar_filename_default(self) -> str:
        """get the name of the default group avatar file for this user."""
        return self.group_avatar_filename() + "_default"

    def create_group_avatar(
        self, s3_client: Any, cipher: Fernet, avatar_bytes: bytes
    ) -> None:
        """Upload an avatar for the group to S3."""
        s3_key = self.group_avatar_s3_key(self.group_avatar_filename())
        upload_image(s3_client, cipher, avatar_bytes, settings.S3_BUCKET_NAME, s3_key)

    def group_avatar_s3_key(self, file_name: str) -> str:
        """Generate the full S3 key for the group avatar."""
        return f"{settings.PROJECT_NAME}/avatars/group/{file_name}.png"

    def remove_group_avatar(self, s3_client: Any) -> None:
        """Remove the avatar for the group."""
        s3_key = self.group_avatar_s3_key(self.group_avatar_filename())
        try:
            s3_client.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=s3_key)
        except ClientError as e:
            logger.error("failed to remove group avatar: %s", str(e))

    def remove_group_avatar_default(self, s3_client: Any) -> None:
        """Remove the default avatar for the group."""
        s3_key = self.group_avatar_s3_key(self.group_avatar_filename_default())
        try:
            s3_client.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=s3_key)
        except ClientError as e:
            logger.error("failed to remove group avatar: %s", str(e))
