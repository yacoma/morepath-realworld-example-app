from argon2 import PasswordHasher

from .model import User


class UserCollection(object):
    def add(self, username, email, password):
        ph = PasswordHasher()
        password_hash = ph.hash(password)
        user = User(username=username, email=email, password=password_hash)
        return user
