from .app import App
from conduit.auth import User


class ViewPermission(object):
    pass


class EditPermission(object):
    pass


@App.permission_rule(model=User, permission=object)
def user_has_self_permission(identity, model, permission):
    return model.email == identity.userid
