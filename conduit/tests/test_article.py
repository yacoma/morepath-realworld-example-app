import json

from argon2 import PasswordHasher
import morepath
from pony.orm import db_session
from webtest import TestApp as Client

import conduit
from conduit import TestApp as App
from conduit.database import db
from conduit.auth import User
from conduit.blog.model import Article, Tag
from conduit.utils import isoformat_to_datetime


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
            bio="My life",
            image="me.png",
        )
        Tag(id=1, tagname="test")
        Tag(id=2, tagname="text")
        Article(
            id=1,
            title="Test text",
            description="About testing",
            body="This is a text test.",
            tag_list=[Tag[1], Tag[2]],
            created_at=isoformat_to_datetime("2017-10-21T13:17:45.000Z"),
            updated_at=isoformat_to_datetime("2017-10-21T15:33:35.000Z"),
            author=User[1],
        )


def test_article():
    c = Client(App())

    article = {
        "slug": "test-text",
        "title": "Test text",
        "description": "About testing",
        "body": "This is a text test.",
        "createdAt": "2017-10-21T13:17:45.000Z",
        "updatedAt": "2017-10-21T15:33:35.000Z",
        "favorited": False,
        "favoritesCount": 0,
        "author": {
            "username": "Tester",
            "bio": "My life",
            "image": "me.png",
            "following": False,
        },
    }

    c.get("/articles/NotExist", status=404)

    response = c.get("/articles/test-text")
    assert article.items() <= response.json["article"].items()
    assert "test" in response.json["article"]["tagList"]
    assert "text" in response.json["article"]["tagList"]

    response = c.post(
        "/users/login",
        json.dumps(
            {"user": {"email": "tester@example.com", "password": "top_secret_1"}}
        ),
    )

    headers = {"Authorization": response.headers["Authorization"]}

    response = c.get("/articles/test-text", headers=headers)

    assert article.items() <= response.json["article"].items()
    assert "test" in response.json["article"]["tagList"]
    assert "text" in response.json["article"]["tagList"]


def test_update_article():
    c = Client(App())

    update_article_json = json.dumps({"article": {"title": "Another story"}})

    c.put("/articles/test-text", update_article_json, status=403)

    response = c.post(
        "/users/login",
        json.dumps(
            {"user": {"email": "tester@example.com", "password": "top_secret_1"}}
        ),
    )

    headers = {"Authorization": response.headers["Authorization"]}

    article = {
        "slug": "another-story",
        "title": "Another story",
        "description": "About testing",
        "body": "This is a text test.",
    }

    response = c.put("/articles/test-text", update_article_json, headers=headers)
    assert article.items() <= response.json["article"].items()
    with db_session:
        assert Article[1].slug == "another-story"

    update_article_json = json.dumps({"article": {"tagList": ["another", "story"]}})

    response = c.put("/articles/another-story", update_article_json, headers=headers)
    assert len(response.json["article"]["tagList"]) == 2
    assert "another" in response.json["article"]["tagList"]
    assert "story" in response.json["article"]["tagList"]

    update_article_json = json.dumps({"article": {"body": 123}})
    response = c.put(
        "/articles/another-story", update_article_json, headers=headers, status=422
    )
    assert response.json == {"errors": {"body": ["must be of string type"]}}


def test_delete_article():
    c = Client(App())

    c.delete("/articles/test-text", status=403)

    response = c.post(
        "/users/login",
        json.dumps(
            {"user": {"email": "tester@example.com", "password": "top_secret_1"}}
        ),
    )

    headers = {"Authorization": response.headers["Authorization"]}

    with db_session:
        assert Article.exists(slug="test-text")

    c.delete("/articles/test-text", headers=headers)

    with db_session:
        assert not Article.exists(slug="test-text")
