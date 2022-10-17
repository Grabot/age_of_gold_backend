from app import db
from datetime import datetime


class Friend(db.Model):
    """
    A connection between one user and another.
    Once this connection is made they can chat with each other
    We assume that they made this connection because they want
    to be friendly with each other, so we classify it as 'Friend'
    """
    __tablename__ = "Friend"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("User.id"))
    friend_id = db.Column(db.Integer, db.ForeignKey("User.id"))
    last_time_activity = db.Column(db.DateTime, default=datetime.utcnow)
    unread_messages = db.Column(db.Integer)
    ignored = db.Column(db.Boolean, default=False)
    removed = db.Column(db.Boolean, default=False)

    def remove(self, deletion):
        self.removed = deletion

    def is_removed(self):
        return self.removed

    @property
    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'friend_id': self.friend_id,
            'last_time_activity': self.last_time_activity.strftime('%Y-%m-%dT%H:%M:%S.%f'),
            'unread_messages': self.unread_messages,
            'ignored': self.ignored
        }

