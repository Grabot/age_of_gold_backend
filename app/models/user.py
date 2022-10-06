from passlib.apps import custom_app_context as pwd_context
from app import db
from flask_login import UserMixin
from app import login
from hashlib import md5
from datetime import datetime


@login.user_loader
def load_user(_id):
    return User.query.get(int(_id))


class User(UserMixin, db.Model):
    """
    User
    """
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text, index=True, unique=False)
    email = db.Column(db.Text, index=True, unique=True)
    password_hash = db.Column(db.Text)
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)

    @property
    def serialize(self):
        """Return object data in easily serializable format"""
        return {
            'id': self.id,
            'username': self.username
        }
