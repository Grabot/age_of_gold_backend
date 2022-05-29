from passlib.apps import custom_app_context as pwd_context
from app.config import Config
from app import db


class User(db.Model):
    """
    User
    """
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text, index=True, unique=False)
    password_hash = db.Column(db.Text)

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    @property
    def serialize(self):
        """Return object data in easily serializable format"""
        return {
            'id': self.id,
            'username': self.username
        }
