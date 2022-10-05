from app import db
from datetime import datetime


# TODO: remove?
#  For now this is purely for debugging, to test out the user login and interaction
class Post(db.Model):
    """
    Post
    """
    __tablename__ = 'Post'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'))

    @property
    def serialize(self):
        """Return object data in easily serializable format"""
        return {
            'id': self.id,
            'body': self.body,
            'user_id': self.user_id,
            'timestamp': self.timestamp.strftime('%Y-%m-%dT%H:%M:%S.%f'),
        }


