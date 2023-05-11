import base64
import os
from passlib.apps import custom_app_context as pwd_context
from authlib.jose import jwt
from app import db
from app.config import DevelopmentConfig, Config
from hashlib import md5
from datetime import datetime
from datetime import timedelta
import time
from sqlalchemy import Index

from app.models.friend import Friend


class User(db.Model):
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
    email = db.Column(db.Text)
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
    tile_lock = db.Column(db.DateTime, default=datetime.utcnow)
    email_verified = db.Column(db.Boolean, default=False)
    default_avatar = db.Column(db.Boolean, default=True)

    __table_args__ = (Index('user_index', "email", "origin", unique=True),)

    def get_tile_lock(self):
        return self.tile_lock

    def lock_tile_setting(self, minutes):
        self.tile_lock = datetime.utcnow() + timedelta(minutes=minutes)

    def can_change_tile_type(self):
        return self.tile_lock <= datetime.utcnow()

    def hash_password(self, password):
        self.password_hash = pwd_context.hash(password)

    def verify_password(self, password):
        print("going to verify")
        # If the user has any other origin than regular it should not get here
        # because the verification is does elsewhere. So if it does, we return False
        print("origin: %s" % self.origin)
        if self.origin != 0:
            return False
        else:
            return pwd_context.verify(password, self.password_hash)

    def set_token(self, token):
        self.token = token

    def set_token_expiration(self, token_expiration):
        self.token_expiration = token_expiration

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)

    def befriend(self, user):
        # Only call if the Friend object is not present yet.
        friend = Friend(
            user_id=self.id,
            friend_id=user.id,
            unread_messages=0
        )
        return friend

    def unfriend(self, user):
        if self.is_friend(user):
            friend = self.friends.filter_by(user_id=self.id, friend_id=user.id).first()
            if friend:
                friend.remove(True)

    def is_friend(self, user):
        if user:
            friend = self.friends.filter_by(user_id=self.id, friend_id=user.id).first()
            if friend:
                return friend.accepted and not friend.removed
            else:
                return False
        else:
            return False

    def generate_auth_token(self, expires_in=3600):
        # also used for email password reset token
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

    def is_verified(self):
        return self.email_verified

    def verify_user(self):
        self.email_verified = True

    def avatar_filename(self):
        return md5(self.email.lower().encode('utf-8')).hexdigest()

    def avatar_filename_small(self):
        return self.avatar_filename() + "_small"

    def avatar_filename_default(self):
        return self.avatar_filename() + "_default"

    def set_new_username(self, new_username):
        self.username = new_username

    def set_default_avatar(self, value):
        self.default_avatar = value

    def is_default(self):
        return self.default_avatar

    def get_user_avatar(self, full=False):
        if self.default_avatar:
            file_name = self.avatar_filename_default()
        else:
            if full:
                file_name = self.avatar_filename()
            else:
                file_name = self.avatar_filename_small()
        file_folder = Config.UPLOAD_FOLDER

        file_path = os.path.join(file_folder, "%s.png" % file_name)
        if not os.path.isfile(file_path):
            return ""
        else:
            with open(file_path, 'rb') as fd:
                image_as_base64 = base64.encodebytes(fd.read()).decode()
            return image_as_base64

    def get_friend_ids(self):
        # Return a list of friend ids, set retrieved to False, so we can retrieve details later.
        return [friend.serialize for friend in self.friends if not friend.removed]

    @property
    def serialize(self):
        # Get detailed user information, mostly used for login
        return {
            'id': self.id,
            'username': self.username,
            'verified': self.email_verified,
            'tile_lock': self.tile_lock.strftime('%Y-%m-%dT%H:%M:%S.%f'),
            'friends': self.get_friend_ids(),
            'avatar': self.get_user_avatar(True),
        }

    @property
    def serialize_get(self):
        # get user details without personal information
        return {
            'id': self.id,
            'username': self.username,
            'avatar': self.get_user_avatar(True),
        }

    @property
    def serialize_minimal(self):
        # get minimal user details
        return {
            'id': self.id,
            'username': self.username,
            'avatar': self.get_user_avatar(False)
        }
