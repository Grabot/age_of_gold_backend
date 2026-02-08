"""Group model."""

from datetime import datetime
from typing import TYPE_CHECKING, Dict, Any
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
    chat_id: int = Field(foreign_key="Chat.id")
    unread_messages: int
    mute: bool = Field(default=False)
    mute_timestamp: Optional[datetime] = Field(default=None)
    last_message_read_id: int = Field(default=0)
    group_version: int = Field(default=1)
    message_version: int = Field(default=1)

    chat: "Chat" = Relationship(
        back_populates="groups",
        sa_relationship_kwargs={
            "uselist": False,
            "primaryjoin": "Chat.id==Group.chat_id",
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
    def serialize(self) -> Dict[str, Any]:
        """Serialize the group data."""
        data = {
            "chat_id": self.chat_id,
            "user_id": self.user_id,
            "unread_messages": self.unread_messages,
            "mute": self.mute,
            "last_message_read_id": self.last_message_read_id,
            "group_version": self.group_version,
            "message_version": self.message_version,
            "avatar_version": self.chat.avatar_version,
            "user_ids": self.chat.user_ids,
            "admin_ids": self.chat.user_admin_ids,
            "name": self.chat.name,
            "private": self.chat.private,
            "description": self.chat.description,
            "colour": self.chat.colour,
            "current_message_id": self.chat.current_message_id,
        }
        return data
