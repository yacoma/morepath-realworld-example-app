from datetime import datetime

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import yaml

import morepath
from more.cerberus import loader

from conduit.permissions import ViewPermission, EditPermission
from .app import App
from .collection import UserCollection
from .model import Login, User, Profile
from .validator import EmailValidator


with open('conduit/auth/schema.yml') as schema:
    schema = yaml.safe_load(schema)

login_validator = loader(schema['login'])
user_validator = loader(schema['user'], EmailValidator)


def _dump_user_json(user, token):
    return {
        'user': {
            'email': user.email,
            'username': user.username,
            'token': token,
            'bio': user.bio,
            'image': user.image
        }
    }


@App.json(model=Login, request_method='POST', load=login_validator)
def login(self, request, json):
    u = json['user']
    email = u['email']
    password = u['password']

    ph = PasswordHasher()
    user = User.get(email=email)
    credentials_valid = False
    if user:
        try:
            ph.verify(user.password, password)
        except VerifyMismatchError:
            pass
        else:
            credentials_valid = True

    if credentials_valid:
        user.last_login = datetime.utcnow()

        @request.after
        def remember(response):
            identity = morepath.Identity(email, username=user.username)
            request.app.remember_identity(response, request, identity)

            # creating JSON view in @request.after to have access to token
            atype, token = response.headers['Authorization'].split(' ', 1)
            response.json = _dump_user_json(user, token)

    else:
        @request.after
        def credentials_not_valid(response):
            response.status_code = 422

        return {
            'errors': {
                'email or password': ['is invalid'],
            }
        }


@App.json(
    model=UserCollection, request_method='POST', load=user_validator
)
def user_add(self, request, json):
    u = json['user']
    email = u['email']
    password = u['password']
    username = u['username']
    errors = {}

    if User.exists(email=email):
        errors['email'] = ['has already been taken']

    if User.exists(username=username):
        errors['username'] = ['has already been taken']

    if errors:
        @request.after
        def after(response):
            response.status = 422

        return {
            'errors': errors
        }

    else:
        user = self.add(
            username=username,
            email=email,
            password=password
        )
        user.last_login = datetime.utcnow()

        @request.after
        def remember(response):
            response.status = 201

            identity = morepath.Identity(email, username=username)
            request.app.remember_identity(response, request, identity)

            # creating JSON view in @request.after to have access to token
            authtype, token = response.headers['Authorization'].split(' ', 1)
            response.json = _dump_user_json(user, token)


@App.json(model=User, permission=ViewPermission)
def user_default(self, request):
    authtype, token = request.headers['Authorization'].split(' ', 1)

    return _dump_user_json(self, token)


@App.json(
    model=User,
    request_method='PUT',
    load=user_validator,
    permission=EditPermission
)
def user_update(self, request, json):
    u = json['user']
    errors = {}

    if 'email' in u and self.email != u['email'] \
            and User.exists(email=u['email']):
        errors['email'] = ['has already been taken']

    if 'username' in u and self.username != u['username'] \
            and User.exists(username=u['username']):
        errors['username'] = ['has already been taken']

    if errors:
        @request.after
        def after(response):
            response.status = 422

        return {
            'errors': errors
        }

    else:
        self.update(u)
        authtype, token = request.headers['Authorization'].split(' ', 1)

        return _dump_user_json(self, token)


def _dump_profile_json(profile, current_user):
    return {
        'profile': {
            'username': profile.profile.username,
            'bio': profile.profile.bio,
            'image': profile.profile.image,
            'following': current_user in profile.profile.followers
            if current_user else False
        }
    }


@App.json(model=Profile)
def profile_default(self, request):
    try:
        current_user = User.get(email=request.identity.userid)
    except ValueError:
        current_user = None

    return _dump_profile_json(self, current_user)


@App.json(
    model=Profile,
    name='follow',
    request_method='POST',
    permission=EditPermission
)
def profile_follow(self, request):
    current_user = User.get(email=request.identity.userid)
    if current_user not in self.profile.followers:
        self.profile.followers.add(current_user)

    return _dump_profile_json(self, current_user)


@App.json(
    model=Profile,
    name='follow',
    request_method='DELETE',
    permission=EditPermission
)
def profile_unfollow(self, request):
    current_user = User.get(email=request.identity.userid)
    if current_user in self.profile.followers:
        self.profile.followers.remove(current_user)

    return _dump_profile_json(self, current_user)
