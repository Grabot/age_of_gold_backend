from typing import List, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship, Column, ARRAY, Integer

if TYPE_CHECKING:
    from src.models import Group

class Chat(SQLModel, table=True):
    """
    Chat
    """

    __tablename__ = "Chat"  # pyright: ignore[reportAssignmentType]
    id: int = Field(default=None, primary_key=True)
    user_ids: List[int] = Field(default=[], sa_column=Column(ARRAY(Integer())))
    user_admin_ids: List[int] = Field(default=[], sa_column=Column(ARRAY(Integer())))
    private: bool = Field(default=True)
    group_name: str
    group_description: str
    group_colour: str
    default_avatar: bool = Field(default=True)
    current_message_id: int
    last_message_read_id_chat: int = Field(default=0)

    groups: List["Group"] = Relationship(
        back_populates="chat",
        sa_relationship_kwargs={
            "uselist": True,
            "primaryjoin": "Chat.id==Group.group_id",
        },
    )
