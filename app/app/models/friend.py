from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class Friend(SQLModel, table=True):
    """
    A connection between one user and another.
    Once this connection is made they can chat with each other
    We assume that they made this connection because they want
    to be friendly with each other, so we classify it as 'Friend'
    """

    __tablename__ = "Friend"
    id: Optional[int] = Field(default=None, primary_key=True)

    user_id: int = Field(foreign_key="User.id")
    friend: "User" = Relationship(
        back_populates="friends",
        sa_relationship_kwargs={
            "primaryjoin": "Friend.user_id == User.id",
        },
    )
    friend_id: int = Field(foreign_key="User.id")
    follower: "User" = Relationship(
        back_populates="followers",
        sa_relationship_kwargs={
            "primaryjoin": "Friend.friend_id == User.id",
        },
    )
    # Store the name of the friend on the friend object
    friend_name: str

    unread_messages: int = Field(default=0)
    accepted: bool = Field(default=False)
    ignored: bool = Field(default=False)
    # Indicates if a request is made or if they are just chatting.
    # If it's filled it determines who made the first move to send the request.
    requested: Optional[bool] = Field(default=None)

    def update_unread_messages(self):
        self.unread_messages += 1

    def read_messages(self):
        self.unread_messages = 0

    @property
    def serialize(self):
        return {
            "id": self.id,
            "friend_id": self.friend_id,
            "unread_messages": self.unread_messages,
            "ignored": self.ignored,
            "accepted": self.accepted,
            "requested": self.requested,
            "friend_name": self.friend_name,
            "friend": self.friend,
            "follower": self.follower,
        }

    @property
    def serialize_minimal(self):
        return {
            "id": self.id,
            "friend_id": self.friend_id,
            "unread_messages": self.unread_messages,
            "ignored": self.ignored,
            "accepted": self.accepted,
            "requested": self.requested,
            "friend_name": self.friend_name,
        }
