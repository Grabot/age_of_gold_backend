from app import db
from datetime import datetime


class GlobalMessage(db.Model):
    __tablename__ = 'GlobalMessage'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    sender_name = db.Column(db.Text)

    @property
    def serialize(self):
        return {
            'body': self.body,
            'sender_name': self.sender_name,
            'timestamp': self.timestamp.strftime('%Y-%m-%dT%H:%M:%S.%f'),
        }


