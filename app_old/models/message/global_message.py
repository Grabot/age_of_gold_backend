from datetime import datetime

from app_old import db


class GlobalMessage(db.Model):
    __tablename__ = "GlobalMessage"
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    sender_name = db.Column(db.Text)
    sender_id = db.Column(db.Integer, db.ForeignKey("User.id"))

    @property
    def serialize(self):
        return {
            "body": self.body,
            "sender_name": self.sender_name,
            "sender_id": self.sender_id,
            "timestamp": self.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f"),
        }
