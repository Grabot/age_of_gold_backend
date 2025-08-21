import time
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class UserToken(SQLModel, table=True):
    """
    UserToken
    """

    __tablename__ = "UserToken"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="User.id")
    access_token: str = Field(index=True)
    token_expiration: int
    refresh_token: str
    refresh_token_expiration: int

    user: "User" = Relationship(back_populates="tokens")  # noqa: F821

    def refresh_is_expired(self) -> bool:
        return self.refresh_token_expiration < int(time.time())
