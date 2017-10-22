from morepath import NO_IDENTITY

from conduit.auth.model import User
from .app import App


class ViewPermission(object):
    pass


class EditPermission(object):
    pass


@App.permission_rule(model=object, permission=object)
def generic_permission(identity, model, permission):
    return identity != NO_IDENTITY


@App.permission_rule(model=User, permission=object)
def user_generic_permission(identity, model, permission):
    return model.email == identity.userid
