import json

from argon2 import PasswordHasher
import morepath
from pony.orm import db_session
from webtest import TestApp as Client

import conduit
from conduit import TestApp as App
from conduit.database import db
from conduit.auth import User


def setup_module(module):
    morepath.scan(conduit)
    morepath.commit(App)


def setup_function(function):
    db.drop_all_tables(with_all_data=True)
    db.create_tables()

    ph = PasswordHasher()

    with db_session:
        User(
            id=1,
            username="Tester",
            email="tester@example.com",
            password=ph.hash("top_secret_1"),
        )
        User(
            id=2,
            username="OtherUser",
            email="other_user@example.com",
            password=ph.hash("top_secret_2"),
        )


def test_profile():
    c = Client(App())

    c.get("/profiles/NotExist", status=404)

    response = c.get("/profiles/OtherUser")

    profile = {
        "profile": {"username": "OtherUser", "bio": "", "image": "", "following": False}
    }

    assert response.json == profile

    response = c.post(
        "/users/login",
        json.dumps(
            {"user": {"email": "tester@example.com", "password": "top_secret_1"}}
        ),
    )

    headers = {"Authorization": response.headers["Authorization"]}
    authtype, token = response.headers["Authorization"].split(" ", 1)

    response = c.get("/profiles/OtherUser", headers=headers)
    profile = {
        "profile": {"username": "OtherUser", "bio": "", "image": "", "following": False}
    }

    assert response.json == profile


def test_profile_follow():
    c = Client(App())

    c.post("/profiles/OtherUser/follow", status=403)

    response = c.post(
        "/users/login",
        json.dumps(
            {"user": {"email": "tester@example.com", "password": "top_secret_1"}}
        ),
    )

    headers = {"Authorization": response.headers["Authorization"]}
    authtype, token = response.headers["Authorization"].split(" ", 1)

    response = c.post("/profiles/OtherUser/follow", headers=headers)
    assert response.json["profile"]["following"] is True

    response = c.post("/profiles/OtherUser/follow", headers=headers)
    assert response.json["profile"]["following"] is True


def test_profile_unfollow():
    c = Client(App())

    c.delete("/profiles/OtherUser/follow", status=403)

    response = c.post(
        "/users/login",
        json.dumps(
            {"user": {"email": "tester@example.com", "password": "top_secret_1"}}
        ),
    )

    headers = {"Authorization": response.headers["Authorization"]}
    authtype, token = response.headers["Authorization"].split(" ", 1)

    response = c.delete("/profiles/OtherUser/follow", headers=headers)
    assert response.json["profile"]["following"] is False

    response = c.post("/profiles/OtherUser/follow", headers=headers)
    assert response.json["profile"]["following"] is True

    response = c.delete("/profiles/OtherUser/follow", headers=headers)
    assert response.json["profile"]["following"] is False
