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
    s = db.Column(db.Integer)
    type = db.Column(db.Integer)

    @property
    def serialize(self):
        """Return object data in easily serializable format"""
        # We don't send the `s` because it can be deduced from q and r
        return {
            'id': self.id,
            'q': self.q,
            'r': self.r,
            'type': self.type
        }
