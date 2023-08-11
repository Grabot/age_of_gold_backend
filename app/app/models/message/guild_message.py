from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class GuildMessage(SQLModel, table=True):
    __tablename__ = "GuildMessage"
    id: Optional[int] = Field(default=None, primary_key=True)

    body: str
    guild_id: int = Field(index=True)
    sender_name: str
    sender_id: int = Field(foreign_key="User.id")
    timestamp: datetime = Field(index=True, default=datetime.utcnow())

    @property
    def serialize(self):
        return {
            "body": self.body,
            "sender_name": self.sender_name,
            "sender_id": self.sender_id,
            "guild_id": self.guild_id,
            "timestamp": self.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f"),
        }
