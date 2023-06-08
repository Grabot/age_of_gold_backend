from typing import List, Optional

from sqlalchemy import Index
from sqlmodel import Field, Relationship, SQLModel


class Hexagon(SQLModel, table=True):
    """
    Hexagon
    """

    __tablename__ = "Hexagon"
    id: Optional[int] = Field(default=None, primary_key=True)
    q: int
    r: int
    tiles_detail: str

    tiles: List["Tile"] = Relationship(
        back_populates="hexagon",
    )

    __table_args__ = (Index("hexagon_index", "q", "r", unique=True),)

    @property
    def serialize(self):
        """Return object data in easily serializable format"""
        # We don't send the `s` because it can be deduced from q and r
        return {"tiles": self.tiles_detail, "q": self.q, "r": self.r}
