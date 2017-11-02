import json

from argon2 import PasswordHasher
import morepath
from pony.orm import db_session
from webtest import TestApp as Client

import conduit
from conduit import TestApp as App
from conduit.database import db
from conduit.auth import User
from conduit.blog.model import Article, Comment
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
            password=ph.hash('top_secret_1'), bio='My life', image='me.png'
        )
        User(
            id=2, username='SomeUser', email='some_user@example.com',
            password=ph.hash('top_secret_2'), follows=[User[1]]
        )
        Article(
            id=1,
            title='Test text',
            description='About testing',
            body='This is a text test.',
            author=User[2]
        )
        Comment(
            id=1,
            body='Cool text.',
            created_at=isoformat_to_datetime('2017-10-21T13:17:45.000Z'),
            updated_at=isoformat_to_datetime('2017-10-21T13:17:45.000Z'),
            author=User[1],
            article=Article[1]
        )
        Comment(
            id=2,
            body='Another comment.',
            created_at=isoformat_to_datetime('2017-10-21T17:54:45.000Z'),
            updated_at=isoformat_to_datetime('2017-10-21T17:54:45.000Z'),
            author=User[2],
            article=Article[1]
        )


def test_list_article_comments():
    c = Client(App())

    comments = {
        'comments': [{
            'id': 2,
            'body': 'Another comment.',
            'createdAt': '2017-10-21T17:54:45.000Z',
            'updatedAt': '2017-10-21T17:54:45.000Z',
            'author': {
                'username': 'SomeUser',
                'bio': '',
                'image': '',
                'following': False
            }
        }, {
            'id': 1,
            'body': 'Cool text.',
            'createdAt': '2017-10-21T13:17:45.000Z',
            'updatedAt': '2017-10-21T13:17:45.000Z',
            'author': {
                'username': 'Tester',
                'bio': 'My life',
                'image': 'me.png',
                'following': False
            }
        }]
    }

    c.get('/articles/NotExist/comments', status=404)

    response = c.get('/articles/test-text/comments')
    assert response.json == comments


def test_add_article_comment():
    c = Client(App())

    new_comment = json.dumps({
        'comment': {
            'body': 'This is a new comment.'
        }
    })

    c.post('/articles/test-text/comments', new_comment, status=403)

    response = c.post(
        '/users/login',
        json.dumps({
            "user": {
                "email": "tester@example.com",
                "password": "top_secret_1"
            }
        }),
    )

    headers = {'Authorization': response.headers['Authorization']}

    comment = {
        'id': 3,
        'body': 'This is a new comment.',
        'author': {
            'username': 'Tester',
            'bio': 'My life',
            'image': 'me.png',
            'following': False
        }
    }

    response = c.post(
        '/articles/test-text/comments', new_comment,
        headers=headers, status=201
    )
    assert comment.items() <= response.json['comment'].items()

    new_comment = json.dumps({
        'comment': {
            'body': 123
        }
    })

    response = c.post(
        '/articles/test-text/comments', new_comment,
        headers=headers, status=422
    )
    assert response.json == {
        'errors': {
            'body': ['must be of string type'],
        }
    }


def test_article_comment():
    c = Client(App())

    comment_1 = {
        'comment': {
            'id': 1,
            'body': 'Cool text.',
            'createdAt': '2017-10-21T13:17:45.000Z',
            'updatedAt': '2017-10-21T13:17:45.000Z',
            'author': {
                'username': 'Tester',
                'bio': 'My life',
                'image': 'me.png',
                'following': True
            }
        }
    }

    comment_2 = {
        'comment': {
            'id': 2,
            'body': 'Another comment.',
            'createdAt': '2017-10-21T17:54:45.000Z',
            'updatedAt': '2017-10-21T17:54:45.000Z',
            'author': {
                'username': 'SomeUser',
                'bio': '',
                'image': '',
                'following': False
            }
        }
    }

    c.get('/articles/NotExist/comments/1', status=404)

    c.get('/articles/test-text/comments/7', status=404)

    response = c.get('/articles/test-text/comments/2')
    assert response.json == comment_2

    response = c.post(
        '/users/login',
        json.dumps({
            "user": {
                "email": "some_user@example.com",
                "password": "top_secret_2"
            }
        }),
    )

    headers = {'Authorization': response.headers['Authorization']}

    response = c.get('/articles/test-text/comments/1', headers=headers)
    assert response.json == comment_1


def test_delete_article_comment():
    c = Client(App())

    c.delete('/articles/test-text/comments/1', status=403)

    response = c.post(
        '/users/login',
        json.dumps({
            "user": {
                "email": "tester@example.com",
                "password": "top_secret_1"
            }
        }),
    )

    headers = {'Authorization': response.headers['Authorization']}

    with db_session:
        assert Comment.exists(id=1)

    response = c.delete('/articles/test-text/comments/1', headers=headers)

    with db_session:
        assert not Comment.exists(id=1)
