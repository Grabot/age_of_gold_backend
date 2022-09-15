from sqlalchemy import Index

from app import db


class Tile(db.Model):
    """
    Tile
    """
    __tablename__ = 'Tile'
    id = db.Column(db.Integer, primary_key=True)
    hexagon_id = db.Column(db.Integer, db.ForeignKey('Hexagon.id'))
    q = db.Column(db.Integer)
    r = db.Column(db.Integer)
    # We no longer require to actually have the 's' indicator s = (q + r) * -1
    # s = db.Column(db.Integer)
    type = db.Column(db.Integer)

    __table_args__ = (
        Index('tile_q_r_index', "q", "r", unique=True),
        Index('tile_id_index', "id", unique=True),
    )

    @property
    def serialize(self):
        """Return object data in easily serializable format"""
        # We don't send the `s` because it can be deduced from q and r
        return {
            'q': self.q,
            'r': self.r,
            'type': self.type
        }
