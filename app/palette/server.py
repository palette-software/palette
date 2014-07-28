from webob import exc

from akiri.framework.ext.sqlalchemy import meta

from page import PalettePage
from rest import PaletteRESTHandler, required_parameters, required_role

from controller.agent import Agent
from controller.agentinfo import AgentVolumesEntry
from controller.profile import Role
from controller.util import sizestr, str2bool

class ServerApplication(PaletteRESTHandler):
    NAME = 'servers'

    # FIXME: allow GETs on all sub-URLs
    def handle(self, req):
        path_info = self.base_path_info(req)
        if path_info == '':
            if req.method == 'GET':
                return self.handle_GET(req)
        elif path_info == 'displayname':
            return self.handle_displayname(req)
        elif path_info == 'archive':
            return self.handle_archive(req)
        elif path_info == 'monitor':
            return self.handle_monitor_POST(req)
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
        value = req.POST['value']
        entry.displayname = value
        meta.Session.commit()
        return {'value':value}

    @required_role(Role.MANAGER_ADMIN)
    @required_parameters('id', 'value')
    def handle_archive(self, req):
        entry = AgentVolumesEntry.get_by_id(req.POST['id'])
        if entry is None:
            raise exc.HTTPNotFound()
        value = str2bool(req.POST['value'])
        entry.archive = value
        meta.Session.commit()
        return {'value':value}

    @required_role(Role.MANAGER_ADMIN)
    @required_parameters('id', 'value')
    def handle_monitor_POST(self, req):
        entry = Agent.get_by_id(req.POST['id'])
        if entry is None:
            raise exc.HTTPNotFound()
        value = str2bool(req.POST['value'])
        entry.enabled = value
        meta.Session.commit()
        return {'value':value}

class ServerConfig(PalettePage):
    TEMPLATE = "server.mako"
    active = 'servers'
    expanded = True
    required_role = Role.READONLY_ADMIN

def make_servers(global_conf):
    return ServerConfig(global_conf)
