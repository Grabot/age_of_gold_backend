"""Friend model"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlmodel import Field, Relationship, SQLModel


if TYPE_CHECKING:
    from src.models import User, Chat


class Friend(SQLModel, table=True):  # type: ignore[call-arg, unused-ignore]
    """
    Friend model representing a friend in the system.
    """

    __tablename__ = "Friend"  # pyright: ignore[reportAssignmentType]
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="User.id")
    accepted: Optional[bool] = Field(default=None)
    friend_version: int = Field(default=1)
    friend_id: int = Field(foreign_key="User.id")
    unread_messages: int = Field(default=0)
    mute: bool = Field(default=False)
    mute_timestamp: Optional[datetime] = Field(default=None)
    last_message_read_id: int = Field(default=0)
    chat_id: int = Field(foreign_key="Chat.id")

    friend: "User" = Relationship(
        back_populates="friends",
        sa_relationship_kwargs={
            "uselist": False,
            "primaryjoin": "User.id==Friend.friend_id",
        },
    )

    chat: "Chat" = Relationship(
        back_populates="friends",
        sa_relationship_kwargs={
            "uselist": False,
            "primaryjoin": "Chat.id==Friend.chat_id",
        },
    )

    @property
    def serialize(self) -> Dict[str, Any]:
        """Serialize the friend object to a dictionary."""
        return {
            "id": self.id,
            "data": {
                "user_id": self.user_id,
                "friend_id": self.friend_id,
                "accepted": self.accepted,
                "chat_id": self.chat_id
            },
        }
