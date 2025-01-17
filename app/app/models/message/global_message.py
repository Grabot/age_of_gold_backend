from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel
import pytz


class GlobalMessage(SQLModel, table=True):
    __tablename__ = "GlobalMessage"
    id: Optional[int] = Field(default=None, primary_key=True)

    body: str
    sender_name: str
    sender_id: int = Field(foreign_key="User.id")
    timestamp: datetime = Field(index=True, default=datetime.now(pytz.utc).replace(tzinfo=None))

    @property
    def serialize(self):
        return {
            "body": self.body,
            "sender_name": self.sender_name,
            "sender_id": self.sender_id,
            "timestamp": self.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f"),
        }
