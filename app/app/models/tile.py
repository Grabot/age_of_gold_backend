from datetime import datetime
from typing import Optional

from sqlalchemy import Index
from sqlmodel import Field, Relationship, SQLModel


class Tile(SQLModel, table=True):
    """
    Tile
    """

    __tablename__ = "Tile"
    id: Optional[int] = Field(default=None, primary_key=True)
    hexagon_id: int = Field(foreign_key="Hexagon.id")
    q: int
    r: int
    type: int
    last_changed_by: Optional[int] = Field(foreign_key="User.id")
    last_changed_time: Optional[datetime]

    hexagon: Optional["Hexagon"] = Relationship(back_populates="tiles")

    __table_args__ = (
        Index("tile_q_r_index", "q", "r", unique=True),
        Index("tile_id_index", "id", unique=True),
    )

    @property
    def serialize(self):
        """Return object data in easily serializable format"""
        return {"q": self.q, "r": self.r, "type": self.type}
