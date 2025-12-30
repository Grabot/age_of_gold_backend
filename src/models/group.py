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
    def serialize_no_chat(self):
        # Used for creating a new broup, we might not have the chat yet.
        data = {
            "group_id": self.group_id,
            "unread_messages": self.unread_messages,
            "mute": self.mute,
            "message_version": self.message_version,
            "group_version": self.group_version,
            "avatar_version": self.avatar_version
        }
        return data