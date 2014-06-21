from webob import exc

from akiri.framework.ext.sqlalchemy import meta
from akiri.environment import Environment
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
        raise exc.HTTPBadMethod()

    def handle_GET(self, req):
        env = Environment.get()
        return {'name': env.name}

    def handle_POST(self, req):
        if 'value' not in req.POST:
            return exc.HTTPBadRequest()
        self.environment.name = req.POST['value']
        meta.Session.commit()
        return {}

