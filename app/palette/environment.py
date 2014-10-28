from webob import exc

# pylint: disable=import-error,no-name-in-module
from akiri.framework.ext.sqlalchemy import meta
# pylint: enable=import-error,no-name-in-module

from controller.environment import Environment
from rest import PaletteRESTHandler

class EnvironmentApplication(PaletteRESTHandler):
    # The REST application will be available at "/rest/environment"
    NAME = 'environment'

    def handle(self, req):
        path_info = self.base_path_info(req)
        if path_info != '':
            raise exc.HTTPNotFound()
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

