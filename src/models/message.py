# from datetime import datetime
# from typing import Optional, List
# from sqlmodel import Field, SQLModel, Column, ARRAY, Integer
# import pytz


# class Message(SQLModel, table=True):
#     """
#     Message
#     """

#     __tablename__ = "Message"  # pyright: ignore[reportAssignmentType]
#     id: Optional[int] = Field(default=None, primary_key=True)
#     sender_id: int = Field(foreign_key="User.id")
#     group_id: int = Field(foreign_key="Chat.id")
#     message_id: int
#     body: str
#     text_message: Optional[str]
#     timestamp: datetime = Field(default=datetime.now(pytz.utc).replace(tzinfo=None))
#     info: bool = Field(default=False)
#     data: Optional[str]
#     data_type: Optional[int]
#     replied_to: Optional[int]
#     receive_remaining: List[int] = Field(default=[], sa_column=Column(ARRAY(Integer())))
#     deleted: bool = Field(default=False)
