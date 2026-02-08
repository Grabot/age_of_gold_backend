"""Chat model."""

from hashlib import md5
from typing import TYPE_CHECKING, Any, List, Optional, Dict

from botocore.exceptions import ClientError
from cryptography.fernet import Fernet
from sqlmodel import Column, Field, Relationship, SQLModel

from src.config.config import settings
from src.models.model_util.zwaar_array import ZwaarArray
from src.util.gold_logging import logger
from src.util.storage_util import upload_image

if TYPE_CHECKING:
    from src.models import Group, Message, Friend


class Chat(SQLModel, table=True):
    """
    Chat
    """

    __tablename__ = "Chat"  # pyright: ignore[reportAssignmentType]
    id: int = Field(default=None, primary_key=True)
    user_ids: List[int] = Field(default=[], sa_column=Column(ZwaarArray()))
    user_admin_ids: List[int] = Field(default=[], sa_column=Column(ZwaarArray()))
    private: bool = Field(default=True)
    name: Optional[str]
    description: Optional[str]
    colour: Optional[str]
    default_avatar: bool = Field(default=True)
    current_message_id: int
    last_message_read_id_chat: int = Field(default=1)
    avatar_version: int = Field(default=1)

    groups: List["Group"] = Relationship(
        back_populates="chat",
        sa_relationship_kwargs={
            "uselist": True,
            "primaryjoin": "Chat.id==Group.chat_id",
        },
    )
    friends: List["Friend"] = Relationship(
        back_populates="chat",
        sa_relationship_kwargs={
            "uselist": True,
            "primaryjoin": "Chat.id==Friend.chat_id",
        },
    )

    messages: List["Message"] = Relationship(
        back_populates="chat",
        sa_relationship_kwargs={
            "uselist": True,
            "primaryjoin": "Chat.id==Message.chat_id",
            "order_by": "Message.created_at",
        },
    )

    def add_user(self, user_id: int) -> None:
        """Add a user to the chat."""
        current_users = self.user_ids or []
        new_users = current_users + [user_id]
        new_users.sort()
        self.user_ids = new_users

    def remove_user(self, user_id: int) -> None:
        """Remove a user from the chat."""
        current_users = self.user_ids or []
        self.user_ids = [
            current_user_id
            for current_user_id in current_users
            if user_id != current_user_id
        ]

    def add_admin(self, user_id: int) -> None:
        """Add an admin to the chat."""
        current_admins = self.user_admin_ids or []
        new_admins = current_admins + [user_id]
        new_admins.sort()
        self.user_admin_ids = new_admins

    def remove_admin(self, user_id: int) -> None:
        """Remove an admin from the chat."""
        current_admins = self.user_admin_ids or []
        self.user_admin_ids = [
            admin_id for admin_id in current_admins if admin_id != user_id
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
