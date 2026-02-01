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
    group_id: int = Field(foreign_key="Chat.id")  # TODO: rename to chat_id?
    unread_messages: int
    mute: bool = Field(default=False)
    mute_timestamp: Optional[datetime] = Field(default=None)
    last_message_read_id: int = Field(default=0)
    group_version: int = Field(default=1)

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
        """Serialize the group data."""
        data = {
            "group_id": self.group_id,
            "user_id": self.user_id,
            "unread_messages": self.unread_messages,
            "mute": self.mute,
            "last_message_read_id": self.last_message_read_id,
            "group_version": self.group_version,
            "message_version": self.chat.message_version,  # pylint: disable=no-member
            "avatar_version": self.chat.avatar_version,  # pylint: disable=no-member
            "user_ids": self.chat.user_ids,  # pylint: disable=no-member
            "admin_ids": self.chat.user_admin_ids,  # pylint: disable=no-member
            "group_name": self.chat.group_name,  # pylint: disable=no-member
            "private": self.chat.private,  # pylint: disable=no-member
            "group_description": self.chat.group_description,  # pylint: disable=no-member
            "group_colour": self.chat.group_colour,  # pylint: disable=no-member
            "current_message_id": self.chat.current_message_id,  # pylint: disable=no-member
        }
        return data
