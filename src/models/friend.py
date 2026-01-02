"""Friend model"""

from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from sqlmodel import Field, Relationship, SQLModel


if TYPE_CHECKING:
    from src.models import User


class Friend(SQLModel, table=True):  # type: ignore[call-arg, unused-ignore]
    """
    Friend model representing a friend in the system.
    """

    __tablename__ = "Friend"  # pyright: ignore[reportAssignmentType]
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="User.id")
    friend_id: int = Field(foreign_key="User.id")
    accepted: bool = Field(default=False)
    friend_version: int = Field(default=1)

    friend: "User" = Relationship(
        back_populates="friends",
        sa_relationship_kwargs={
            "uselist": False,
            "primaryjoin": "User.id==Friend.friend_id",
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
                "accepted": self.accepted
            }
        }
