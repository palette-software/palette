""" Applications for accessing the system table. """
# pylint: enable=relative-import,missing-docstring

from webob import exc

from akiri.framework import GenericWSGIApplication, ENVIRON_PREFIX
import akiri.framework.sqlalchemy as meta

from controller.profile import Role

from .rest import required_parameters, required_role, status_ok

class SystemApplication(GenericWSGIApplication):
    """ System table REST API endpoint. """

    @required_role(Role.READONLY_ADMIN)
    def service_GET(self, req):
        """ Handle a HTTP GET request. """
        environ_key = ENVIRON_PREFIX + 'key'
        if environ_key in req.environ:
            key = req.environ[environ_key]
            if not key in req.system:
                raise exc.HTTPNotFound("No such key : '" + key + "'")
            return status_ok(value=req.system[key])
        data = status_ok()
        for key in sorted(req.system.keys()):
            data[key] = req.system[key]
        return data

    @required_parameters('value')
    def post_one(self, req, key):
        """ Handle a HTTP POST request for a specific key. """
        if not key in req.system:
            raise exc.HTTPNotFound("No such key : '" + key + "'")
        req.system[key] = req.POST['value']
        meta.commit()
        return status_ok()

    @required_role(Role.MANAGER_ADMIN)
    def service_POST(self, req):
        """ Handle a HTTP POST request. """
        environ_key = ENVIRON_PREFIX + 'key'
        if environ_key in req.environ:
            return self.post_one(req, req.environ[environ_key])
        keys = []
        for key in req.POST:
            if not key in req.system:
                raise exc.HTTPBadRequest("Invalid system key : '" + key + "'")
            keys.append(key)
        if not keys:
            raise exc.HTTPBadRequest("No system keys specified.")
        for key in keys:
            req.system[key] = req.POST[key]
        meta.commit()
        return status_ok()

