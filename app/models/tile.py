from sqlalchemy import Index
from app.models.user import User
from app import db
from datetime import datetime


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
    last_changed_by = db.Column(db.Integer, db.ForeignKey('User.id'))
    last_changed_time = db.Column(db.DateTime)

    __table_args__ = (
        Index('tile_q_r_index', "q", "r", unique=True),
        Index('tile_id_index', "id", unique=True),
    )

    def update_tile_info(self, tile_type, user_id):
        self.type = tile_type
        self.last_changed_by = user_id
        self.last_changed_time = datetime.utcnow()
        print("updated tile!")

    @property
    def serialize_full(self):
        user_info = None
        if self.last_changed_by:
            user = User.query.filter_by(id=self.last_changed_by).first()
            if user:
                user_info = user.serialize
        last_time = None
        if self.last_changed_time:
            last_time = self.last_changed_time.strftime('%Y-%m-%dT%H:%M:%S.%f')
        print("getting full tile info %s, %s" % (user_info, last_time))
        return {
            'q': self.q,
            'r': self.r,
            'type': self.type,
            'last_changed_by': user_info,
            'last_changed_time': last_time,
        }

    @property
    def serialize(self):
        """Return object data in easily serializable format"""
        # We don't send the `s` because it can be deduced from q and r
        return {
            'q': self.q,
            'r': self.r,
            'type': self.type
        }
