from argon2 import PasswordHasher

from .model import User


class UserCollection:
    def add(self, username, email, password):
        ph = PasswordHasher()
        password_hash = ph.hash(password)

        return User(username=username, email=email, password=password_hash)
