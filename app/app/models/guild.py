import base64
import os
from hashlib import md5
from typing import List, Optional

from sqlalchemy import ARRAY, Column, Integer
from sqlmodel import Field, Relationship, SQLModel

from app.config.config import settings


class Guild(SQLModel, table=True):
    """
    A connection between one user and it's guild.
    With this guild object they can access the guild functionality.
    """

    __tablename__ = "Guild"
    id: Optional[int] = Field(default=None, primary_key=True)
    guild_id: int = Field(index=True)

    user_id: int = Field(foreign_key="User.id")
    guild_member: "User" = Relationship(
        back_populates="guild",
        sa_relationship_kwargs={
            "uselist": False,
            "primaryjoin": "User.id==Guild.user_id",
        },
    )

    guild_name: str
    default_crest: bool = Field(default=True)

    # members of the guild with their guild rank.
    # So [[1, 0], [2, 1]] would mean that user 1 is the guild leader and user 2 is a member
    member_ids: List[List[int]] = Field(default=[[]], sa_column=Column(ARRAY(Integer())))
    unread_messages: int = Field(default=0)

    accepted: bool = Field(default=False)
    # Indicates if a request is made
    requested: Optional[bool] = Field(default=None)

    def update_unread_messages(self):
        self.unread_messages += 1

    def read_messages(self):
        self.unread_messages = 0

    def crest_filename(self):
        return md5(self.guild_name.lower().encode("utf-8")).hexdigest()

    def get_guild_crest(self):
        if self.default_crest:
            return None
        else:
            file_folder = settings.UPLOAD_FOLDER_CRESTS

            file_name = self.crest_filename()

            file_path = os.path.join(file_folder, "%s.png" % file_name)
            if not os.path.isfile(file_path):
                return None
            else:
                with open(file_path, "rb") as fd:
                    image_as_base64 = base64.encodebytes(fd.read()).decode()
                return image_as_base64

    @property
    def serialize(self):
        return {
            "guild_id": self.guild_id,
            "user_id": self.user_id,
            "unread_messages": self.unread_messages,
            "guild_name": self.guild_name,
            "guild_crest": self.get_guild_crest(),
            "members": self.member_ids,
            "accepted": self.accepted,
            "requested": self.requested,
        }

    @property
    def serialize_minimal(self):
        # The guild without the member and crest information
        return {
            "guild_id": self.guild_id,
            "user_id": self.user_id,
            "unread_messages": self.unread_messages,
            "guild_name": self.guild_name,
            "accepted": self.accepted,
            "requested": self.requested,
        }
