from datetime import datetime
from slugify import UniqueSlugify
from pony.orm import PrimaryKey, Required, Optional, Set, LongStr

from conduit.auth import User
from conduit.database import db


class Article(db.Entity):
    _table_ = 'articles'

    slug = Optional(str, 200, unique=True, nullable=True, default=None)
    title = Required(str, 255)
    description = Required(LongStr)
    body = Required(LongStr)
    created_at = Required(datetime, 0, default=datetime.utcnow)
    updated_at = Required(datetime, 0, default=datetime.utcnow)
    author = Required(User, reverse="articles")
    favorited = Set(User, reverse="favorites")
    comments = Set("Comment")
    tag_list = Set("Tag")

    def _unique_check(self, text, uids):
        if text in uids:
            return False
        return not self.__class__.exists(slug=text)

    def _slugify_url_unique(self, text):
        slugify_url_unique = UniqueSlugify(
            unique_check=self._unique_check, uids=['feed']
        )
        slugify_url_unique.to_lower = True
        slugify_url_unique.stop_words = ('a', 'an', 'the')
        slugify_url_unique.max_length = 200
        return slugify_url_unique(text)

    def before_insert(self):
        if not self.slug:
            self.slug = self._slugify_url_unique(self.title)

    def before_update(self):
        self.updated_at = datetime.utcnow()

    def update(self, payload={}):
        update_payload = {}
        for attribute, value in payload.items():
            if attribute == 'tagList':
                tags = []
                for tagname in value:
                    tag = Tag.get(tagname=tagname)
                    if not tag:
                        tag = Tag(tagname=tagname)
                    tags.append(tag)
                update_payload['tag_list'] = tags
            else:
                update_payload[attribute] = value

            if attribute == 'title' and value != self.title:
                self.slug = self._slugify_url_unique(value)

        self.set(**update_payload)

    def remove(self):
        self.delete()


class Comment(db.Entity):
    _table_ = 'comments'

    id = PrimaryKey(int, auto=True)
    body = Required(LongStr)
    created_at = Required(datetime, 0, default=datetime.utcnow)
    updated_at = Required(datetime, 0, default=datetime.utcnow)
    author = Required(User)
    article = Required(Article)

    def remove(self):
        self.delete()


class Tag(db.Entity):
    _table_ = 'tags'

    tagname = Required(str, 255)
    articles = Set(Article)
