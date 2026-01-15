"""Group model."""

from datetime import datetime
from typing import TYPE_CHECKING
from typing import Optional
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from src.models import Chat
    from src.models import User


class Group(SQLModel, table=True):
    """
    User group
    """

    __tablename__ = "Group"  # pyright: ignore[reportAssignmentType]
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="User.id")
    group_id: int = Field(foreign_key="Chat.id")
    unread_messages: int
    mute: bool = Field(default=False)
    mute_timestamp: Optional[datetime] = Field(default=None)
    group_version: int = Field(default=1)
    message_version: int = Field(default=1)
    avatar_version: int = Field(default=1)
    last_message_read_id: int = Field(default=0)

    chat: "Chat" = Relationship(
        back_populates="groups",
        sa_relationship_kwargs={
            "uselist": False,
            "primaryjoin": "Chat.id==Group.group_id",
        },
    )

    group_member: "User" = Relationship(
        back_populates="groups",
        sa_relationship_kwargs={
            "uselist": False,
            "primaryjoin": "User.id==Group.user_id",
        },
    )

    @property
    def serialize(self):
        # Used for creating a new broup, we might not have the chat yet.
        data = {
            "group_id": self.group_id,
            "unread_messages": self.unread_messages,
            "mute": self.mute,
            "mute_timestamp": self.mute_timestamp,
            "group_version": self.group_version,
            "message_version": self.message_version,
            "avatar_version": self.avatar_version,
            "last_message_read_id": self.last_message_read_id,
            "user_ids": self.chat.user_ids,
            "admin_ids": self.chat.user_admin_ids,
            "group_name": self.chat.group_name,
            "private": self.chat.private,
            "group_description": self.chat.group_description,
            "group_colour": self.chat.group_colour,
            "current_message_id": self.chat.current_message_id
        }
        return data
