from morepath import NO_IDENTITY
from webob.exc import HTTPUnauthorized

from .app import App
from .collection import UserCollection
from .model import Login, User


@App.path(model=Login, path='users/login')
def get_login():
    return Login()


@App.path(model=User, path='user')
def get_current_user(request):
    current_user = request.identity
    if current_user == NO_IDENTITY:
        raise HTTPUnauthorized

    return User.get(email=current_user.userid)


@App.path(model=UserCollection, path='users')
def get_user_collection():
    return UserCollection()
