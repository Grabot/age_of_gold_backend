from datetime import datetime

from app import db


class PersonalMessage(db.Model):
    __tablename__ = "PersonalMessage"
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("User.id"))
    receiver_id = db.Column(db.Integer, db.ForeignKey("User.id"))

    @property
    def serialize(self):
        return {
            "body": self.body,
            "user_id": self.user_id,
            "receiver_id": self.receiver_id,
            "timestamp": self.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f"),
        }
