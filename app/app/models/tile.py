from datetime import datetime
from typing import Optional

from sqlalchemy import Index
from sqlmodel import Field, Relationship, SQLModel
import pytz


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

    hexagon: "Hexagon" = Relationship(back_populates="tiles")
    user_changed: Optional["User"] = Relationship(
        back_populates="tiles_changed",
    )

    __table_args__ = (
        Index("tile_q_r_index", "q", "r", unique=True),
        Index("tile_id_index", "id", unique=True),
    )

    def update_tile_info(self, tile_type, user_id):
        self.type = tile_type
        self.last_changed_by = user_id
        self.last_changed_time = datetime.now(pytz.utc).replace(tzinfo=None)

    @property
    def serialize_full(self):
        user_info = None
        if self.user_changed:
            user_info = self.user_changed.serialize_minimal
        last_time = None
        if self.last_changed_time:
            last_time = self.last_changed_time.strftime("%Y-%m-%dT%H:%M:%S.%f")
        return {
            "q": self.q,
            "r": self.r,
            "type": self.type,
            "last_changed_by": user_info,
            "last_changed_time": last_time,
        }

    @property
    def serialize(self):
        """Return object data in easily serializable format"""
        return {"q": self.q, "r": self.r, "type": self.type}
