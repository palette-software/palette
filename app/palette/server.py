from webob import exc

from akiri.framework.ext.sqlalchemy import meta

from page import PalettePage
from rest import PaletteRESTHandler, required_parameters

from controller.agentstatus import AgentStatusEntry

class ServerApplication(PaletteRESTHandler):
    NAME = 'servers'

    def handle(self, req):
        path_info = self.base_path_info(req)
        if path_info == '':
            if req.method == 'GET':
                return self.handle_GET(req)
        elif path_info == 'displayname':
            if req.method == 'POST':
                return self.handle_displayname(req)
        raise exc.HTTPMethodNotAllowed()

    def handle_GET(self, req):
        exclude = ['username', 'password']
        L = meta.Session.query(AgentStatusEntry).all()
        return {'servers': [x.todict(pretty=True, exclude=exclude) for x in L],
                'environment' : self.environment.name}

    @required_parameters('id', 'value')
    def handle_displayname(self, req):
        entry = AgentStatusEntry.get_by_id(req.POST['id'])
        if entry is None:
            raise exc.HTTPNotFound()
        entry.displayname = req.POST['value']
        meta.Session.commit()
        return {}

class ServerConfig(PalettePage):
    TEMPLATE = "server.mako"
    active = 'servers'
    expanded = True

def make_servers(global_conf):
    return ServerConfig(global_conf)
