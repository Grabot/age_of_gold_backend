from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class Guild(SQLModel, table=True):
    """
    A connection between one user and it's guild.
    With this guild object they can access the guild functionality.
    """

    __tablename__ = "Guild"
    id: Optional[int] = Field(default=None, primary_key=True)

    user_id: int = Field(foreign_key="User.id")
    guild_member: "User" = Relationship(
        back_populates="guild",
        sa_relationship_kwargs={
            "primaryjoin": "Guild.user_id == User.id",
        },
    )

    guild_name: str
    guild_crest: Optional[str]

    member_ids: List[int] = Field(default=[])

    @property
    def serialize(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "guild_name": self.guild_name,
            "guild_crest": self.guild_crest,
        }
