import yaml

from more.cerberus import loader

from conduit.permissions import EditPermission
from conduit.auth import User
from conduit.utils import datetime_to_isoformat
from .app import App
from .collection import ArticleCollection, ArticleFeed, CommentCollection, TagCollection
from .model import Article, Comment


with open("conduit/blog/schema.yml") as schema:
    schema = yaml.safe_load(schema)

article_validator = loader(schema["article"])
comment_validator = loader(schema["comment"])


def _dump_article_json(article, current_user=None):
    return {
        "article": {
            "slug": article.slug,
            "title": article.title,
            "description": article.description,
            "body": article.body,
            "tagList": [tag.tagname for tag in article.tag_list],
            "createdAt": datetime_to_isoformat(article.created_at),
            "updatedAt": datetime_to_isoformat(article.updated_at),
            "favorited": current_user in article.favorited if current_user else False,
            "favoritesCount": len(article.favorited),
            "author": {
                "username": article.author.username,
                "bio": article.author.bio,
                "image": article.author.image,
                "following": current_user in article.author.followers
                if current_user
                else False,
            },
        }
    }


@App.json(model=ArticleCollection)
def article_collection_default(self, request):
    articles = [request.view(article)["article"] for article in self.query()]

    return {"articles": articles, "articlesCount": len(articles)}


@App.json(model=ArticleFeed)
def article_feed_default(self, request):
    articles = [request.view(article)["article"] for article in self.query()]

    return {"articles": articles, "articlesCount": len(articles)}


@App.json(
    model=ArticleCollection,
    request_method="POST",
    load=article_validator,
    permission=EditPermission,
)
def article_add(self, request, json):
    a = json["article"]
    title = a["title"]
    description = a["description"]
    body = a["body"]
    tag_list = a.get("tagList", [])
    current_user = User.get(email=request.identity.userid)

    article = self.add(
        title=title,
        description=description,
        body=body,
        author=current_user,
        tag_list=tag_list,
    )

    @request.after
    def remember(response):
        response.status = 201

    return _dump_article_json(article, current_user)


@App.json(model=Article)
def article_default(self, request):
    try:
        current_user = User.get(email=request.identity.userid)
    except ValueError:
        current_user = None

    return _dump_article_json(self, current_user)


@App.json(
    model=Article,
    request_method="PUT",
    load=article_validator,
    permission=EditPermission,
)
def article_update(self, request, json):
    self.update(json["article"])
    current_user = User.get(email=request.identity.userid)

    return _dump_article_json(self, current_user)


@App.json(model=Article, request_method="DELETE", permission=EditPermission)
def article_remove(self, request):
    self.remove()


@App.json(
    model=Article, name="favorite", request_method="POST", permission=EditPermission
)
def article_favorite(self, request):
    current_user = User.get(email=request.identity.userid)
    if current_user not in self.favorited:
        self.favorited.add(current_user)

    return _dump_article_json(self, current_user)


@App.json(
    model=Article, name="favorite", request_method="DELETE", permission=EditPermission
)
def article_unfavorite(self, request):
    current_user = User.get(email=request.identity.userid)
    if current_user in self.favorited:
        self.favorited.remove(current_user)

    return _dump_article_json(self, current_user)


def _dump_comment_json(comment, current_user=None):
    return {
        "comment": {
            "id": comment.id,
            "body": comment.body,
            "createdAt": datetime_to_isoformat(comment.created_at),
            "updatedAt": datetime_to_isoformat(comment.updated_at),
            "author": {
                "username": comment.author.username,
                "bio": comment.author.bio,
                "image": comment.author.image,
                "following": current_user in comment.author.followers
                if current_user
                else False,
            },
        }
    }


@App.json(model=CommentCollection)
def comment_collection_default(self, request):
    return {"comments": [request.view(comment)["comment"] for comment in self.query()]}


@App.json(
    model=CommentCollection,
    request_method="POST",
    load=comment_validator,
    permission=EditPermission,
)
def comment_add(self, request, json):
    c = json["comment"]
    body = c["body"]
    current_user = User.get(email=request.identity.userid)

    comment = self.add(body=body, author=current_user)

    @request.after
    def remember(response):
        response.status = 201

    return _dump_comment_json(comment, current_user)


@App.json(model=Comment, internal=True)
def comment_default(self, request):
    try:
        current_user = User.get(email=request.identity.userid)
    except ValueError:
        current_user = None

    return _dump_comment_json(self, current_user)


@App.json(model=Comment, request_method="DELETE", permission=EditPermission)
def comment_remove(self, request):
    self.remove()


@App.json(model=TagCollection)
def tag_collection_default(self, request):
    return {"tags": [tag.tagname for tag in self.query()]}
