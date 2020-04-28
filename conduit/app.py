import yaml

from more.jwtauth import JWTIdentityPolicy
from more.pony import PonyApp
from more.cors import CORSApp

from conduit.auth import AuthApp
from conduit.blog import BlogApp


class App(PonyApp, AuthApp, BlogApp, CORSApp):
    pass


with open('conduit/settings/default.yml') as defaults:
    defaults_dict = yaml.safe_load(defaults)

App.init_settings(defaults_dict)


@App.identity_policy()
def get_identity_policy(settings):
    jwtauth_settings = settings.jwtauth.__dict__.copy()
    return JWTIdentityPolicy(**jwtauth_settings)


@App.verify_identity()
def verify_identity(identity):
    return True


class ProductionApp(App):
    pass


with open('conduit/settings/production.yml') as settings:
    settings_dict = yaml.safe_load(settings)

ProductionApp.init_settings(settings_dict)


class TestApp(App):
    pass


with open('conduit/settings/test.yml') as settings:
    settings_dict = yaml.safe_load(settings)

TestApp.init_settings(settings_dict)
