from sqlalchemy import Index

from app_old import db


class Hexagon(db.Model):
    """
    Hexagon
    """

    __tablename__ = "Hexagon"
    id = db.Column(db.Integer, primary_key=True)
    tiles = db.relationship("Tile", backref="tile")
    q = db.Column(db.Integer)
    r = db.Column(db.Integer)
    # We no longer require to actually have the 's' indicator s = (q + r) * -1
    # s = db.Column(db.Integer)
    tiles_detail = db.Column(db.Text)

    __table_args__ = (Index("hexagon_index", "q", "r", unique=True),)

    @property
    def serialize(self):
        """Return object data in easily serializable format"""
        # We don't send the `s` because it can be deduced from q and r
        return {"tiles": self.tiles_detail, "q": self.q, "r": self.r}
