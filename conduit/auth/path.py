from morepath import NO_IDENTITY
from webob.exc import HTTPUnauthorized, HTTPNotFound

from .app import App
from .collection import UserCollection
from .model import Login, User, Profile


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


@App.path(model=Profile, path='profiles/{username}')
def get_profile(username):
    user = User.get(username=username)
    if not user:
        raise HTTPNotFound

    return Profile(user)
