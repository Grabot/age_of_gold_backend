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
    unread_messages = db.Column(db.Integer, default=0)
    accepted = db.Column(db.Boolean, default=False)
    ignored = db.Column(db.Boolean, default=False)
    # Indicates if a request is made or if they are just chatting and who made the first move to send the request
    requested = db.Column(db.Boolean, default=None, nullable=True)

    def is_accepted(self):
        return self.accepted

    def add_unread_message(self):
        self.unread_messages += 1

    @property
    def serialize(self):
        from app.models.user import User

        friend = User.query.filter_by(id=self.friend_id).first()
        friend_detail = None
        if friend is not None:
            friend_detail = friend.serialize_minimal
        return {
            "id": self.id,
            "friend": friend_detail,
            "last_time_activity": self.last_time_activity.strftime(
                "%Y-%m-%dT%H:%M:%S.%f"
            ),
            "unread_messages": self.unread_messages,
            "ignored": self.ignored,
            "accepted": self.accepted,
            "requested": self.requested,
        }
