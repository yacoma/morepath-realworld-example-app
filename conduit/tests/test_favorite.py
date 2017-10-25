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
            id=1, username='Tester', email='tester@example.com',
            password=ph.hash('test1'), bio='My life', image='me.png'
        )
        User(id=2, username='SomeUser', email='some_user@example.com',
             password=ph.hash('test2'), follows=[User[1]])
        Tag(id=1, tagname='test')
        Article(
            id=1,
            title='Test text',
            description='About testing',
            body='This is a text test.',
            tag_list=[Tag[1]],
            created_at=isoformat_to_datetime('2017-10-21T13:17:45.000Z'),
            updated_at=isoformat_to_datetime('2017-10-21T15:33:35.000Z'),
            author=User[2]
        )


def test_article_favorite():
    c = Client(App())

    c.post('/articles/test-text/favorite', status=403)

    response = c.post(
        '/users/login',
        json.dumps({
            "user": {
                "email": "tester@example.com",
                "password": "test1"
            }
        }),
    )

    headers = {'Authorization': response.headers['Authorization']}

    response = c.post('/articles/test-text/favorite', headers=headers)
    assert response.json['article']['favorited'] is True

    response = c.post('/articles/test-text/favorite', headers=headers)
    assert response.json['article']['favorited'] is True


def test_article_unfavorite():
    c = Client(App())

    c.delete('/articles/test-text/favorite', status=403)

    response = c.post(
        '/users/login',
        json.dumps({
            "user": {
                "email": "tester@example.com",
                "password": "test1"
            }
        }),
    )

    headers = {'Authorization': response.headers['Authorization']}

    response = c.delete('/articles/test-text/favorite', headers=headers)
    assert response.json['article']['favorited'] is False

    response = c.post('/articles/test-text/favorite', headers=headers)
    assert response.json['article']['favorited'] is True

    response = c.delete('/articles/test-text/favorite', headers=headers)
    assert response.json['article']['favorited'] is False
