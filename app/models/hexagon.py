from app import db
from sqlalchemy import types


class Hexagon(db.Model):
    """
    Hexagon
    """
    __tablename__ = 'Hexagon'
    id = db.Column(db.Integer, primary_key=True)
    tiles = db.relationship("Tile", backref="tile")
    q = db.Column(db.Integer)
    r = db.Column(db.Integer)
    s = db.Column(db.Integer)
    tiles_detail = db.Column(db.Text)

    @property
    def serialize(self):
        """Return object data in easily serializable format"""
        # We don't send the `s` because it can be deduced from q and r
        return {
            'tiles': self.tiles_detail,
            'q': self.q,
            'r': self.r
        }
