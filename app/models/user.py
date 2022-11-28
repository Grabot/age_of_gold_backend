from authlib.jose.errors import DecodeError
from passlib.apps import custom_app_context as pwd_context
from authlib.jose import jwt
from app import db, auth
from app.config import DevelopmentConfig
from flask_login import UserMixin
from app import login
from hashlib import md5
from datetime import datetime
from app.models.friend import Friend
import time


@login.user_loader
def load_user(_id):
    return User.query.get(int(_id))


def refresh_user_token(access_token, refresh_token):
    access = None
    refresh = None
    try:
        access = jwt.decode(access_token, DevelopmentConfig.jwk)
        refresh = jwt.decode(refresh_token, DevelopmentConfig.jwk)
    except DecodeError:
        print("decode error, big fail!")
        return None

    if not access or not refresh:
        print("big fail!")
        return None

    # The access token should be active
    user = User.query.filter_by(token=access_token).first()
    print('access: %s' % access)
    print('refresh: %s' % refresh)
    if user is None or refresh["exp"] < int(time.time()):
        return None

    # It all needs to match before you send back new tokens
    if user.id == access["id"] and user.username == refresh["user_name"]:
        print("it's all good! Send more tokens")
        return user
    else:
        return None


def check_token(token):
    user = User.query.filter_by(token=token).first()
    if user is None or user.token_expiration < int(time.time()):
        return None
    return user


def get_user_tokens(user, access_expiration=3600, refresh_expiration=36000):
    # Create an access_token that the user can use to do user authentication
    access_token = user.generate_auth_token(access_expiration).decode('ascii')
    # Create a refresh token that lasts longer that the user can use to generate a new access token
    refresh_token = user.generate_refresh_token(refresh_expiration).decode('ascii')
    # Only store the access token, refresh token is kept client side
    user.set_token(access_token)
    return [access_token, refresh_token]


class User(UserMixin, db.Model):
    """
    User
    """
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True)
    # friends of the user
    friends = db.relationship(
        'Friend',
        foreign_keys=[Friend.user_id],
        backref=db.backref('followers', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan')
    # other friends that have befriended this user
    # A friend connection makes 2 'Friend' entries, each of these lists corresponds to the different direction
    followers = db.relationship(
        'Friend',
        foreign_keys=[Friend.friend_id],
        backref=db.backref('friends', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan')
    username = db.Column(db.Text, index=True, unique=True)
    # The user can use the same email with a different origin.
    # The email and origin is unique
    # TODO: Make email and origin unique.
    email = db.Column(db.Text, index=True)
    password_hash = db.Column(db.Text)
    about_me = db.Column(db.Text)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    # Keep track of how the user logged in
    # 0 = regular
    # 1 = google login
    # 2 = gitHub login
    # 3 = reddit login
    origin = db.Column(db.Integer)
    token = db.Column(db.Text, index=True)
    token_expiration = db.Column(db.Integer)

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        # If the user has any other origin than regular it should not get here
        # because the verification is does elsewhere. So if it does, we return False
        if self.origin != 0:
            return False
        else:
            return pwd_context.verify(password, self.password_hash)

    def set_token(self, token):
        self.token = token

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)

    def befriend(self, user):
        friend = self.friends.filter_by(user_id=self.id, friend_id=user.id).first()
        if not friend:
            friend = Friend(
                user_id=self.id,
                friend_id=user.id,
                last_time_activity=datetime.utcnow(),
                unread_messages=0,
                ignored=False,
                removed=False
            )
            db.session.add(friend)
            return friend
        else:
            if friend.is_removed():
                friend.remove(False)
                db.session.add(friend)
                return friend
            else:
                return friend

    def unfriend(self, user):
        if self.is_friend(user):
            friend = self.friends.filter_by(user_id=self.id, friend_id=user.id).first()
            if friend:
                friend.remove(True)
                db.session.add(friend)

    def is_friend(self, user):
        if user:
            friend = self.friends.filter_by(user_id=self.id, friend_id=user.id).first()
            if friend:
                return not friend.is_removed()
            else:
                return False
        else:
            return False

    def generate_auth_token(self, expires_in=3600):
        payload = {
            "id": self.id,
            "iss": DevelopmentConfig.JWT_ISS,
            "aud": DevelopmentConfig.JWT_AUD,
            "sub": DevelopmentConfig.JWT_SUB,
            "exp": int(time.time()) + expires_in,  # expiration time
            "iat": int(time.time())  # issued at
        }
        return jwt.encode(DevelopmentConfig.header, payload, DevelopmentConfig.jwk)

    def generate_refresh_token(self, expires_in=36000):
        payload = {
            "user_name": self.username,
            "iss": DevelopmentConfig.JWT_ISS,
            "aud": DevelopmentConfig.JWT_AUD,
            "sub": DevelopmentConfig.JWT_SUB,
            "exp": int(time.time()) + expires_in,  # expiration time
            "iat": int(time.time())  # issued at
        }
        return jwt.encode(DevelopmentConfig.header, payload, DevelopmentConfig.jwk)

    @property
    def serialize(self):
        """Return object data in easily serializable format"""
        return {
            'id': self.id,
            'username': self.username
        }
