from webob import exc

# pylint: disable=import-error,no-name-in-module
from akiri.framework.ext.sqlalchemy import meta
# pylint: enable=import-error,no-name-in-module

from controller.environment import Environment
from .rest import PaletteRESTApplication

class EnvironmentApplication(PaletteRESTApplication):
    def service(self, req):
        if req.method == 'GET':
            return self.handle_GET(req)
        if req.method == 'POST':
            return self.handle_POST(req)
        raise exc.HTTPMethodNotAllowed()

    # pylint: disable=invalid-name
    def handle_GET(self, req):
        # pylint: disable=unused-argument
        entry = Environment.get()
        return {'name': entry.name}

    def handle_POST(self, req):
        if 'value' not in req.POST:
            return exc.HTTPBadRequest()
        entry = Environment.get()
        entry.name = req.POST['value']
        meta.Session.commit()
        return {}

