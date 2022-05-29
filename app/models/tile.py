from app import db


class Tile(db.Model):
    """
    Tile
    """
    __tablename__ = 'Tile'
    id = db.Column(db.Integer, primary_key=True)
    hexagon_id = db.Column(db.Integer, db.ForeignKey('Hexagon.id'))
    type = db.Column(db.Integer)

    @property
    def serialize(self):
        """Return object data in easily serializable format"""
        return {
            'id': self.id,
            'type': self.type
        }
