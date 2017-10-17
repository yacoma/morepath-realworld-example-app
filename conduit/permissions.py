from morepath import NO_IDENTITY

from conduit.auth.model import User, Profile
from .app import App


class ViewPermission(object):
    pass


class EditPermission(object):
    pass


@App.permission_rule(model=User, permission=object)
def user_has_self_permission(identity, model, permission):
    return model.email == identity.userid


@App.permission_rule(model=Profile, permission=object)
def is_authenticated(identity, model, permission):
    return identity != NO_IDENTITY
