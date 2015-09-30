""" Base classes and functions for REST endpoints. """
# pylint: enable=relative-import,missing-docstring

from collections import OrderedDict

from webob import exc

from akiri.framework import GenericWSGIApplication

from controller.profile import Role
from controller.palapi import CommHandlerApp
from controller.util import prettyify

def status_ok(**kwargs):
    """ Create a successful response dict() """
    res = OrderedDict({u'status': u'OK'})
    for arg in kwargs:
        res[prettyify(arg)] = kwargs[arg]
    return res

def status_failed(error, **kwargs):
    """ Create an error response dict() """
    res = OrderedDict({u'status': 'FAILED', u'error': error})
    for arg in kwargs:
        res[prettyify(arg)] = kwargs[arg]
    return res

def required_parameters(*params):
    """Decorator for POST handlers that throws a 400 error if a required
    parameter is missing from the request."""
    def wrapper(f):
        """ wrapper docstring """
        def realf(self, req, *args, **kwargs):
            """ realf docstring """
            if req.method != 'POST':
                raise exc.HTTPMethodNotAllowed(req.method)
            for param in params:
                if param not in req.POST:
                    raise exc.HTTPBadRequest("'" + param + "' missing")
            return f(self, req, *args, **kwargs)
        return realf
    return wrapper

def required_role(name):
    """Decorator to specify a minimum permission needed for this endpoint."""
    def wrapper(f):
        """ wrapper docstring """
        def realf(self, req, *args, **kwargs):
            """ realf docstring """
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
