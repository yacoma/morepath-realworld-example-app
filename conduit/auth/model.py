from datetime import datetime
from argon2 import PasswordHasher
from pony.orm import Required, Optional, Set

from conduit.database import db


class Login:
    pass


class User(db.Entity):
    _table_ = 'users'

    username = Required(str, 80, unique=True)
    email = Required(str, 100, unique=True)
    password = Required(str, 255)
    registered = Required(datetime, 0, default=datetime.utcnow)
    last_login = Optional(datetime, 0)
    bio = Optional(str, 300)
    image = Optional(str, 120)
    followers = Set("User", reverse="follows")
    follows = Set("User", reverse="followers")
    articles = Set("Article", reverse="author")
    favorites = Set("Article", reverse="favorited")
    comments = Set("Comment")

    def update(self, payload={}):
        update_payload = {}
        for attribute, value in payload.items():
            if attribute == 'password':
                ph = PasswordHasher()
                password_hash = ph.hash(value)
                update_payload['password'] = password_hash
            else:
                update_payload[attribute] = value
        self.set(**update_payload)


class Profile:
    def __init__(self, user):
        self.profile = user
