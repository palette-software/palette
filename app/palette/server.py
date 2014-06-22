from webob import exc

from akiri.framework.ext.sqlalchemy import meta

from page import PalettePage
from rest import PaletteRESTHandler, required_parameters, required_role

from controller.agent import Agent
from controller.agentinfo import AgentVolumesEntry
from controller.profile import Role
from controller.util import sizestr

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
        elif path_info == 'archive':
            if req.method == 'POST':
                return self.handle_archive(req)
        raise exc.HTTPMethodNotAllowed()

    def volumes(self, server):
        volumes = []
        for volume in server.volumes:
            d = volume.todict(pretty=True)
            if not 'used' in d:
                continue
            if volume.archive:
                d['checkbox-state'] = 'checked'
            volumes.append(d)
        return volumes

    def handle_GET(self, req):
        exclude = ['username', 'password']
        L = meta.Session.query(Agent).order_by(Agent.display_order).all()

        servers = []
        for server in L:
            d = server.todict(pretty=True, exclude=exclude)
            d['volumes'] = self.volumes(server)
            servers.append(d)

        return {'servers': servers,
                'environment' : self.environment.name}

    @required_role(Role.MANAGER_ADMIN)
    @required_parameters('id', 'value')
    def handle_displayname(self, req):
        entry = Agent.get_by_id(req.POST['id'])
        if entry is None:
            raise exc.HTTPNotFound()
        entry.displayname = req.POST['value']
        meta.Session.commit()
        return {}

    @required_role(Role.MANAGER_ADMIN)
    @required_parameters('id', 'value')
    def handle_archive(self, req):
        entry = AgentVolumesEntry.get_by_id(req.POST['id'])
        if entry is None:
            raise exc.HTTPNotFound()
        entry.archive = bool(req.POST['value'])
        meta.Session.commit()
        return {}

class ServerConfig(PalettePage):
    TEMPLATE = "server.mako"
    active = 'servers'
    expanded = True
    required_role = Role.READONLY_ADMIN

def make_servers(global_conf):
    return ServerConfig(global_conf)
