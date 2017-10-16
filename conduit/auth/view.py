from datetime import datetime

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import yaml

import morepath
from more.cerberus import loader

from conduit.permissions import ViewPermission, EditPermission
from .app import App
from .collection import UserCollection
from .model import Login, User
from .validator import EmailValidator


with open('conduit/auth/schema.yml') as schema:
    schema = yaml.load(schema)

login_validator = loader(schema['login'])
user_validator = loader(schema['user'], EmailValidator)


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
            user.last_login = datetime.now()

            @request.after
            def remember(response):
                identity = morepath.Identity(email, username=user.username)
                request.app.remember_identity(response, request, identity)

                atype, token = response.headers['Authorization'].split(' ', 1)
                response_json = {
                    'user': {
                        'email': user.email,
                        'username': user.username,
                        'token': token,
                        'bio': user.bio,
                        'image': user.image
                    }
                }
                response.json = response_json

        else:
            @request.after
            def credentials_not_valid(response):
                response.status_code = 403

            return {'validationError': 'Invalid email or password'}

    else:
        @request.after
        def credentials_not_valid(response):
            response.status_code = 403

        return {'validationError': 'Invalid email or password'}


@App.json(model=User, permission=ViewPermission)
def user_get(self, request):
    authtype, token = request.headers['Authorization'].split(' ', 1)
    return {
        'user': {
            'email': self.email,
            'username': self.username,
            'token': token,
            'bio': self.bio,
            'image': self.image
        }
    }


@App.json(
    model=UserCollection, request_method='POST', load=user_validator
)
def user_collection_add(self, request, json):
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
        user.last_login = datetime.now()

        @request.after
        def remember(response):
            response.status = 201

            identity = morepath.Identity(email, username=username)
            request.app.remember_identity(response, request, identity)

            authtype, token = response.headers['Authorization'].split(' ', 1)
            response_json = {
                'user': {
                    'email': user.email,
                    'username': user.username,
                    'token': token,
                    'bio': user.bio,
                    'image': user.image
                }
            }
            response.json = response_json


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

        return {
            'user': {
                'email': self.email,
                'username': self.username,
                'token': token,
                'bio': self.bio,
                'image': self.image
            }
        }
