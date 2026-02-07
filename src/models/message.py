"""Message model."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional, List
import pytz
from sqlmodel import Field, SQLModel, Column, ARRAY, Integer, Relationship

if TYPE_CHECKING:
    from src.models import Chat


class Message(SQLModel, table=True):
    """
    Message model for storing chat messages.
    """

    __tablename__ = "Message"  # pyright: ignore[reportAssignmentType]
    id: int = Field(default=None, primary_key=True)
    chat_id: int = Field(foreign_key="Chat.id")
    sender_id: int
    content: str
    created_at: datetime = Field(default=datetime.now(pytz.utc).replace(tzinfo=None))
    message_type: int = Field(default=0)
    replied_to: Optional[int]
    receive_remaining: List[int] = Field(default=[], sa_column=Column(ARRAY(Integer())))
    deleted: bool = Field(default=False)

    # Chat relationship
    chat: "Chat" = Relationship(
        back_populates="messages",
        sa_relationship_kwargs={
            "uselist": False,
            "primaryjoin": "Chat.id==Message.chat_id",
        },
    )

    def received_message(self, user_id):
        current_received = self.receive_remaining or []
        self.receive_remaining = [
            current_user_id
            for current_user_id in current_received
            if user_id != current_user_id
        ]

    @property
    def serialize(self) -> dict:
        """Serialize the message data."""
        data = {
            "id": self.id,
            "chat_id": self.chat_id,
            "sender_id": self.sender_id,
            "content": self.content,
            "created_at": self.created_at.strftime("%Y-%m-%dT%H:%M:%S.%f"),
            "message_type": self.message_type,
        }
        if self.replied_to is not None:
            data["replied_to"] = self.replied_to
        if self.deleted:
            data["deleted"] = self.deleted
        return data
