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
            id=2,
            username="OtherUser",
            email="other_user@example.com",
            password=ph.hash("top_secret_2"),
        )
        User(
            id=1,
            username="Tester",
            email="tester@example.com",
            password=ph.hash("top_secret_1"),
            bio="My life",
            image="me.png",
            follows=[User[2]],
        )
        Tag(id=1, tagname="test")
        Tag(id=2, tagname="text")
        Article(
            id=1,
            title="Test text",
            description="About testing",
            body="This is a text test.",
            tag_list=[Tag[1]],
            created_at=isoformat_to_datetime("2017-10-21T13:17:45.000Z"),
            updated_at=isoformat_to_datetime("2017-10-21T15:33:35.000Z"),
            author=User[1],
        )
        Article(
            id=2,
            title="Second text",
            description="More about testing",
            body="This is another text.",
            tag_list=[Tag[2]],
            created_at=isoformat_to_datetime("2017-10-22T13:55:34.000Z"),
            updated_at=isoformat_to_datetime("2017-10-22T15:59:22.000Z"),
            author=User[2],
            favorited=[User[1]],
        )


def test_add_article():
    c = Client(App())

    new_article = json.dumps(
        {
            "article": {
                "title": "New text",
                "description": "News about testing",
                "body": "This is a new text.",
                "tagList": ["news", "text"],
            }
        }
    )

    c.post("/articles", new_article, status=403)

    response = c.post(
        "/users/login",
        json.dumps(
            {"user": {"email": "tester@example.com", "password": "top_secret_1"}}
        ),
    )

    headers = {"Authorization": response.headers["Authorization"]}

    article = {
        "slug": "new-text",
        "title": "New text",
        "description": "News about testing",
        "body": "This is a new text.",
        "favorited": False,
        "favoritesCount": 0,
        "author": {
            "username": "Tester",
            "bio": "My life",
            "image": "me.png",
            "following": False,
        },
    }

    response = c.post("/articles", new_article, headers=headers, status=201)
    assert article.items() <= response.json["article"].items()
    assert "news" in response.json["article"]["tagList"]
    assert "text" in response.json["article"]["tagList"]

    with db_session:
        assert Article.exists(slug="new-text")
        assert Tag[3].tagname == "news"

    response = c.post("/articles", new_article, headers=headers, status=201)
    assert response.json["article"]["slug"] == "new-text-1"

    new_article = json.dumps(
        {
            "article": {
                "title": "Feed",
                "description": "Feeding your child",
                "body": "What's about breast feeding?",
            }
        }
    )

    response = c.post("/articles", new_article, headers=headers, status=201)
    assert response.json["article"]["slug"] == "feed-1"

    new_article = json.dumps(
        {
            "article": {
                "title": 123,
                "description": False,
                "body": 789,
                "tagList": [12345],
            }
        }
    )

    response = c.post("/articles", new_article, headers=headers, status=422)
    assert response.json == {
        "errors": {
            "title": ["must be of string type"],
            "description": ["must be of string type"],
            "body": ["must be of string type"],
            "tagList": [{"0": ["must be of string type"]}],
        }
    }


def test_list_articles():
    c = Client(App())

    article_1 = {
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
        "tagList": ["test"],
    }

    article_2 = {
        "slug": "second-text",
        "title": "Second text",
        "description": "More about testing",
        "body": "This is another text.",
        "createdAt": "2017-10-22T13:55:34.000Z",
        "updatedAt": "2017-10-22T15:59:22.000Z",
        "favorited": False,
        "favoritesCount": 1,
        "author": {"username": "OtherUser", "bio": "", "image": "", "following": False},
        "tagList": ["text"],
    }

    response = c.get("/articles")
    assert len(response.json["articles"]) == 2
    assert response.json["articles"][0] == article_2
    assert response.json["articles"][1] == article_1


def test_filter_articles():
    c = Client(App())

    article_1 = {
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
        "tagList": ["test"],
    }

    article_2 = {
        "slug": "second-text",
        "title": "Second text",
        "description": "More about testing",
        "body": "This is another text.",
        "createdAt": "2017-10-22T13:55:34.000Z",
        "updatedAt": "2017-10-22T15:59:22.000Z",
        "favorited": False,
        "favoritesCount": 1,
        "author": {"username": "OtherUser", "bio": "", "image": "", "following": False},
        "tagList": ["text"],
    }

    response = c.get("/articles?tag=test")
    assert len(response.json["articles"]) == 1
    assert response.json["articles"][0] == article_1

    response = c.get("/articles?author=Tester")
    assert len(response.json["articles"]) == 1
    assert response.json["articles"][0] == article_1

    response = c.get("/articles?favorited=Tester")
    assert len(response.json["articles"]) == 1
    assert response.json["articles"][0] == article_2


def test_paginate_articles():
    c = Client(App())

    article_1 = {
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
        "tagList": ["test"],
    }

    article_2 = {
        "slug": "second-text",
        "title": "Second text",
        "description": "More about testing",
        "body": "This is another text.",
        "createdAt": "2017-10-22T13:55:34.000Z",
        "updatedAt": "2017-10-22T15:59:22.000Z",
        "favorited": False,
        "favoritesCount": 1,
        "author": {"username": "OtherUser", "bio": "", "image": "", "following": False},
        "tagList": ["text"],
    }

    response = c.get("/articles?limit=1")
    assert len(response.json["articles"]) == 1
    assert response.json["articles"][0] == article_2

    response = c.get("/articles?limit=1&offset=1")
    assert len(response.json["articles"]) == 1
    assert response.json["articles"][0] == article_1


def test_feed_articles():
    c = Client(App())

    article_2 = {
        "slug": "second-text",
        "title": "Second text",
        "description": "More about testing",
        "body": "This is another text.",
        "createdAt": "2017-10-22T13:55:34.000Z",
        "updatedAt": "2017-10-22T15:59:22.000Z",
        "favorited": True,
        "favoritesCount": 1,
        "author": {"username": "OtherUser", "bio": "", "image": "", "following": True},
        "tagList": ["text"],
    }

    c.get("/articles/feed", status=401)

    response = c.post(
        "/users/login",
        json.dumps(
            {"user": {"email": "tester@example.com", "password": "top_secret_1"}}
        ),
    )

    headers = {"Authorization": response.headers["Authorization"]}

    response = c.get("/articles/feed", headers=headers)
    assert len(response.json["articles"]) == 1
    assert response.json["articles"][0] == article_2


def test_paginate_feed_articles():
    c = Client(App())

    article_2 = {
        "slug": "second-text",
        "title": "Second text",
        "description": "More about testing",
        "body": "This is another text.",
        "createdAt": "2017-10-22T13:55:34.000Z",
        "updatedAt": "2017-10-22T15:59:22.000Z",
        "favorited": True,
        "favoritesCount": 1,
        "author": {"username": "OtherUser", "bio": "", "image": "", "following": True},
        "tagList": ["text"],
    }

    response = c.post(
        "/users/login",
        json.dumps(
            {"user": {"email": "tester@example.com", "password": "top_secret_1"}}
        ),
    )

    headers = {"Authorization": response.headers["Authorization"]}

    response = c.get("/articles/feed?limit=1", headers=headers)
    assert len(response.json["articles"]) == 1
    assert response.json["articles"][0] == article_2

    response = c.get("/articles/feed?limit=1&offset=1", headers=headers)
    assert len(response.json["articles"]) == 0
