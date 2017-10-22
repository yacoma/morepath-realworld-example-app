import morepath
from pony.orm import db_session
from webtest import TestApp as Client

import conduit
from conduit import TestApp as App
from conduit.database import db
from conduit.blog.model import Tag


def setup_module(module):
    morepath.scan(conduit)
    morepath.commit(App)


def setup_function(function):
    db.drop_all_tables(with_all_data=True)
    db.create_tables()

    with db_session:
        Tag(id=1, tagname='test')
        Tag(id=2, tagname='text')


def test_list_tags():
    c = Client(App())

    response = c.get('/tags')
    assert len(response.json['tags']) == 2
    assert 'test' in response.json['tags']
    assert 'text' in response.json['tags']
