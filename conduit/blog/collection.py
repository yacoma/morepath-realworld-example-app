from pony.orm import desc

from conduit.auth import User
from .model import Article, Comment, Tag


class ArticleCollection(object):
    def __init__(self, tag, author, favorited, limit, offset):
        self.tag = Tag.get(tagname=tag) if tag else None
        self.author = User.get(username=author) if author else None
        self.favorited = User.get(username=favorited) if favorited else None
        self.limit = limit
        self.offset = offset

    def query(self):
        result = Article.select()
        if self.tag:
            result = result.where(lambda a: self.tag in a.tag_list)
        if self.author:
            result = result.where(lambda a: a.author == self.author)
        if self.favorited:
            result = result.where(lambda a: self.favorited in a.favorited)
        result = result.sort_by(desc(Article.created_at))
        if self.limit:
            result = result.limit(self.limit, offset=self.offset)

        return result[:]

    def add(self, title, description, body, author, tag_list):
        tags = []
        if tag_list:
            for tagname in tag_list:
                tag = Tag.get(tagname=tagname)
                if not tag:
                    tag = Tag(tagname=tagname)
                tags.append(tag)

        article = Article(
            title=title,
            description=description,
            body=body,
            author=author,
            tag_list=tags
        )
        article.flush()

        return article


class ArticleFeed(object):
    def __init__(self, user, limit, offset):
        self.user = user
        self.limit = limit
        self.offset = offset

    def query(self):
        result = Article.select(lambda a: self.user in a.author.followers)
        result = result.sort_by(desc(Article.created_at))
        if self.limit:
            result = result.limit(self.limit, offset=self.offset)

        return result[:]


class CommentCollection(object):
    def __init__(self, article):
        self.article = article

    def query(self):
        return Comment.select(
            lambda c: c.article == self.article
        ).sort_by(desc(Comment.created_at))[:]

    def add(self, body, author):
        comment = Comment(
            body=body,
            author=author,
            article=self.article
        )
        comment.flush()

        return comment


class TagCollection(object):
    def query(self):
        return Tag.select().sort_by(Tag.tagname)[:]
