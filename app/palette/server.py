from webob import exc

# pylint: disable=import-error,no-name-in-module
from akiri.framework.ext.sqlalchemy import meta
# pylint: enable=import-error,no-name-in-module

from .page import PalettePage
from .rest import required_parameters, required_role, PaletteRESTApplication

from controller.agent import Agent, AgentVolumesEntry
from controller.agentmanager import AgentManager
from controller.licensing import LicenseEntry
from controller.profile import Role
from controller.util import str2bool
from controller.yml import YmlEntry

class ServerApplication(PaletteRESTApplication):
    # FIXME: allow GETs on all sub-URLs
    def service(self, req):
        if 'action' in req.environ:
            action = req.environ['action']
            if action == 'displayname':
                return self.handle_displayname(req)
            elif action == 'archive':
                return self.handle_archive(req)
            elif action == 'monitor':
                return self.handle_monitor_POST(req)
            raise exc.HTTPNotFound()

        if req.method == 'GET':
            return self.handle_GET(req)
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
        query = meta.Session.query(Agent)
        query = query.order_by(Agent.display_order).order_by(Agent.displayname)

        servers = []
        for server in query.all():
            d = server.todict(pretty=True, exclude=exclude)
            d['volumes'] = self.volumes(server)
            d['type-name'] = AgentManager.get_type_name(server.agent_type)

            entry = LicenseEntry.get_by_agentid(server.agentid)
            if not entry is None:
                d['tableau-license-type'] = entry.gettype()
                capacity = entry.capacity()
                if capacity:
                    d['tableau-license-capacity'] = capacity

            if server.agent_type == AgentManager.AGENT_TYPE_PRIMARY:
                version = YmlEntry.get(req.envid, 'version.external',
                                       default=None)
                if version:
                    d['tableau-version'] = version
                bitness = YmlEntry.get(req.envid,
                                       'version.bitness',
                                            default=None)
                if bitness:
                    d['tableau-bitness'] = bitness

            servers.append(d)

        name = req.environ['PALETTE_ENVIRONMENT'].name
        return {'servers': servers, 'environment': name}

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
    # pylint: disable=invalid-name
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
