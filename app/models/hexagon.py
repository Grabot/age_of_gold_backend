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

    @property
    def serialize(self):
        """Return object data in easily serializable format"""
        tiles_info = []
        for tile in self.tiles:
            tiles_info.append(tile.serialize)
        return {
            'id': self.id,
            'tiles': tiles_info,
            'q': self.q,
            'r': self.r,
            's': self.s
        }
