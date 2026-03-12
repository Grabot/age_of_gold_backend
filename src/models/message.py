"""Message model."""

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Optional, List
from src.config.config import settings
from sqlmodel import Field, SQLModel, Column, Relationship

from src.models.model_util.zwaar_array import ZwaarArray
from src.util.storage_util import media_s3_key, download_media

if TYPE_CHECKING:
    from src.models import Chat


class Message(SQLModel, table=True):
    """
    Message model for storing chat messages.
    """

    __tablename__ = "Message"  # type: ignore[assignment]
    id: int = Field(default=None, primary_key=True)
    message_id: int = Field(default=0)
    chat_id: int = Field(foreign_key="Chat.id")
    sender_id: int
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    message_type: int = Field(default=0)
    replied_to: Optional[int] = Field(default=None)
    receive_remaining: List[int] = Field(default=[], sa_column=Column(ZwaarArray()))
    remove_at: Optional[datetime] = Field(default_factory=None) # Indicates when to remove from the backend
    deleted: Optional[int] = Field(default=None) # Indicates which message_id has been removed.
    message_data: Optional[str] = Field(default=None)

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

    def received_by_all(self):
        return len(self.receive_remaining) == 0

    def set_for_deletion(self):
        self.remove_at = datetime.now() + timedelta(days=settings.MESSAGE_REMOVE_TIME)


    def get_message_data(self, s3_client, cipher) -> bytes | None:
        if not self.message_data:
            print("No message data available")
            return None
        s3_key = media_s3_key(f"{self.message_data}")
        print(f"Downloading file {s3_key}")
        return download_media(s3_client, cipher, settings.S3_BUCKET_NAME, s3_key)


    def serialize(self) -> dict:
        """Serialize the message data."""
        created_at_str = self.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        data = {
            "id": self.message_id,
            "chat_id": self.chat_id,
            "sender_id": self.sender_id,
            "content": self.content,
            "created_at": created_at_str,
            "message_type": self.message_type,
        }
        if self.replied_to is not None:
            data["replied_to"] = self.replied_to
        if self.deleted:
            data["deleted"] = self.deleted
        return data
