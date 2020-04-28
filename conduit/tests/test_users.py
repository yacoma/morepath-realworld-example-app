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


def test_login():
    app = App()
    c = Client(app)

    response = c.post(
        "/users/login",
        json.dumps(
            {"user": {"email": "tester@example.com", "password": "false_password"}}
        ),
        status=422,
    )
    assert response.json == {"errors": {"email or password": ["is invalid"]}}

    response = c.post(
        "/users/login",
        json.dumps(
            {"user": {"email": "not_exists@example.com", "password": "top_secret_1"}}
        ),
        status=422,
    )
    assert response.json == {"errors": {"email or password": ["is invalid"]}}

    response = c.post(
        "/users/login",
        json.dumps(
            {"user": {"email": "tester@example.com", "password": "top_secret_1"}}
        ),
    )

    authtype, token = response.headers["Authorization"].split(" ", 1)
    user = {
        "user": {
            "email": "tester@example.com",
            "username": "Tester",
            "token": token,
            "bio": "",
            "image": "",
        }
    }

    assert response.json == user


def test_user():
    c = Client(App())

    c.get("/user", status=401)

    response = c.post(
        "/users/login",
        json.dumps(
            {"user": {"email": "tester@example.com", "password": "top_secret_1"}}
        ),
    )

    headers = {"Authorization": response.headers["Authorization"]}
    authtype, token = response.headers["Authorization"].split(" ", 1)

    response = c.get("/user", headers=headers)
    user = {
        "user": {
            "email": "tester@example.com",
            "username": "Tester",
            "token": token,
            "bio": "",
            "image": "",
        }
    }

    assert response.json == user


def test_add_user():
    c = Client(App(), extra_environ=dict(REMOTE_ADDR="127.0.0.1"))

    new_user_json = json.dumps(
        {
            "user": {
                "username": "NewUser",
                "email": "newuser@example.com",
                "password": "top_secret_3",
            }
        }
    )

    response = c.post("/users", new_user_json, status=201)
    authtype, token = response.headers["Authorization"].split(" ", 1)
    user = {
        "user": {
            "email": "newuser@example.com",
            "username": "NewUser",
            "token": token,
            "bio": "",
            "image": "",
        }
    }

    assert response.json == user
    with db_session:
        assert User.exists(username="NewUser")

    new_user_json = json.dumps(
        {
            "user": {
                "username": "NextUser",
                "email": "newuser@example.com",
                "password": "top_secret_3",
            }
        }
    )

    response = c.post("/users", new_user_json, status=422)
    assert response.json == {"errors": {"email": ["has already been taken"]}}

    new_user_json = json.dumps(
        {
            "user": {
                "username": "NewUser",
                "email": "nextuser@example.com",
                "password": "top_secret_3",
            }
        }
    )

    response = c.post("/users", new_user_json, status=422)
    assert response.json == {"errors": {"username": ["has already been taken"]}}

    new_user_json = json.dumps(
        {
            "user": {
                "username": "NewUser",
                "email": "newuser@example",
                "password": "top_secret_4",
            }
        }
    )

    response = c.post("/users", new_user_json, status=422)
    assert response.json == {"errors": {"email": ["Not valid email"]}}

    new_user_json = json.dumps(
        {
            "user": {
                "username": 123,
                "email": "username_not_string@example.com",
                "password": "top_secret_5",
            }
        }
    )

    response = c.post("/users", new_user_json, status=422)
    assert response.json == {"errors": {"username": ["must be of string type"]}}

    new_user_json = json.dumps(
        {
            "user": {
                "username": "next_user",
                "email": "username_not_string@example.com",
                "password": "short",
            }
        }
    )

    response = c.post("/users", new_user_json, status=422)
    assert response.json == {"errors": {"password": ["min length is 8"]}}


def test_update_user():
    c = Client(App())

    response = c.post(
        "/users/login",
        json.dumps(
            {"user": {"email": "tester@example.com", "password": "top_secret_1"}}
        ),
    )

    headers = {"Authorization": response.headers["Authorization"]}
    authtype, token = response.headers["Authorization"].split(" ", 1)

    update_user_json = json.dumps(
        {"user": {"username": "Guru", "bio": "My life", "image": "avatar.png"}}
    )
    response = c.put("/user", update_user_json, headers=headers)
    user = {
        "user": {
            "email": "tester@example.com",
            "username": "Guru",
            "token": token,
            "bio": "My life",
            "image": "avatar.png",
        }
    }

    assert response.json == user
    with db_session:
        assert User[1].username == "Guru"

    update_user_json = json.dumps({"user": {"email": "guru@example"}})
    response = c.put("/user", update_user_json, headers=headers, status=422)
    assert response.json == {"errors": {"email": ["Not valid email"]}}

    update_user_json = json.dumps({"user": {"email": "other_user@example.com"}})
    response = c.put("/user", update_user_json, headers=headers, status=422)
    assert response.json == {"errors": {"email": ["has already been taken"]}}

    update_user_json = json.dumps({"user": {"username": "OtherUser"}})
    response = c.put("/user", update_user_json, headers=headers, status=422)
    assert response.json == {"errors": {"username": ["has already been taken"]}}

    update_user_json = json.dumps({"user": {"password": "top_secret_0"}})
    c.put("/user", update_user_json, headers=headers)

    ph = PasswordHasher()
    with db_session:
        assert ph.verify(User[1].password, "top_secret_0")

    update_user_json = json.dumps({"user": {"email": "guru@example.com"}})
    c.put("/user", update_user_json, headers=headers)

    with db_session:
        assert User[1].email == "guru@example.com"
