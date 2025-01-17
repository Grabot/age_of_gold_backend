from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel
import pytz

class PersonalMessage(SQLModel, table=True):
    __tablename__ = "PersonalMessage"
    id: Optional[int] = Field(default=None, primary_key=True)

    body: str
    user_id: int = Field(foreign_key="User.id")
    receiver_id: int = Field(foreign_key="User.id")
    timestamp: datetime = Field(index=True, default=datetime.now(pytz.utc).replace(tzinfo=None))

    @property
    def serialize(self):
        return {
            "body": self.body,
            "user_id": self.user_id,
            "receiver_id": self.receiver_id,
            "timestamp": self.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f"),
        }
