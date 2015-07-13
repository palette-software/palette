from webob import exc

from akiri.framework import GenericWSGIApplication

from controller.profile import Role
from controller.palapi import CommHandlerApp

def required_parameters(*params):
    def wrapper(f):
        def realf(self, req, *args, **kwargs):
            if req.method != 'POST':
                raise exc.HTTPMethodNotAllowed(req.method)
            for param in params:
                if param not in req.POST:
                    raise exc.HTTPBadRequest("'" + param + "' missing")
            return f(self, req, *args, **kwargs)
        return realf
    return wrapper

def required_role(name):
    def wrapper(f):
        def realf(self, req, *args, **kwargs):
            if isinstance(name, basestring):
                role = Role.get_by_name(name).roleid
            else:
                role = Role.get_by_roleid(name)
            if req.remote_user.roleid < role.roleid:
                raise exc.HTTPForbidden("The '"+role.name+"' role is required.")
            return f(self, req, *args, **kwargs)
        return realf
    return wrapper


class PaletteRESTApplication(GenericWSGIApplication):
    """Base class for all REST handlers."""
    def __init__(self):
        super(PaletteRESTApplication, self).__init__()
        self.commapp = CommHandlerApp(self)
