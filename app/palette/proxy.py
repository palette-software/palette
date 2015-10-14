"""Proxy wrapper - primarily for contacting licensing."""
# pylint: enable=missing-docstring,relative-import

from webob import exc

from akiri.framework import GenericWSGIApplication

from controller.licensing import licensing_hello

class LicensingHelloProxy(GenericWSGIApplication):
    """ Proxy requests to licensing.palette-software.com """

    def service_GET(self, req):
        """ Try to contact licensing/hello """
        status_code = licensing_hello(req.system)
        if status_code != 200:
            details = 'licensing returned status-code : ' + str(status_code)
            raise exc.HTTPNotFound(details)
        return {'status': 'OK'}
