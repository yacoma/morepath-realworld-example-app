from morepath import NO_IDENTITY
from webob.exc import HTTPUnauthorized, HTTPNotFound

from conduit.auth import User
from .app import App
from .collection import (
    ArticleCollection, ArticleFeed, CommentCollection, TagCollection
)
from .model import Article, Comment


@App.path(model=ArticleCollection, path='articles')
def get_article_collection(
    tag='',
    author='',
    favorited='',
    limit=20,
    offset=0
):
    return ArticleCollection(tag, author, favorited, limit, offset)


@App.path(model=ArticleFeed, path='articles/feed')
def get_article_feed(request, limit=20, offset=0):
    current_user = request.identity
    if current_user == NO_IDENTITY:
        raise HTTPUnauthorized
    user = User.get(email=current_user.userid)

    return ArticleFeed(user, limit, offset)


@App.path(model=Article, path='articles/{slug}')
def get_article(slug=''):
    return Article.get(slug=slug)


@App.path(model=CommentCollection, path='articles/{slug}/comments')
def get_comment_collection(slug=''):
    article = Article.get(slug=slug)
    if not article:
        raise HTTPNotFound
    return CommentCollection(article)


@App.path(model=Comment, path='articles/{slug}/comments/{id}')
def get_comment(slug='', id=0):
    article = Article.get(slug=slug)
    if not article or not Comment.exists(id=id):
        raise HTTPNotFound
    return Comment[id]


@App.path(model=TagCollection, path='tags')
def get_tag_collection():
    return TagCollection()
