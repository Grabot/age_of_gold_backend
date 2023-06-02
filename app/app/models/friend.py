from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Friend(SQLModel, table=True):
    """
    A connection between one user and another.
    Once this connection is made they can chat with each other
    We assume that they made this connection because they want
    to be friendly with each other, so we classify it as 'Friend'
    """

    __tablename__ = "Friend"
    id: Optional[int] = Field(default=None, primary_key=True)

    user_id: Optional[int] = Field(default=None, foreign_key="User.id")
    friend_id: Optional[int] = Field(default=None, foreign_key="User.id")

    last_time_activity: datetime = Field(default=datetime.utcnow())
    unread_messages: int = Field(default=0)
    accepted: bool = Field(default=False)
    ignored: bool = Field(default=False)
    # Indicates if a request is made or if they are just chatting.
    # If it's filled it determines who made the first move to send the request.
    requested: Optional[bool] = Field(default=None)
