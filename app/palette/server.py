from akiri.framework.ext.sqlalchemy import meta

from page import PalettePage
from rest import PaletteRESTHandler

from controller.agentstatus import AgentStatusEntry

class ServerApplication(PaletteRESTHandler):
    NAME = 'servers'

    def handle(self, req):
        L = meta.Session.query(AgentStatusEntry).all()
        return {'servers': [x.todict(pretty=True) for x in L],
                'environment' : self.environment.name}

class ServerConfig(PalettePage):
    TEMPLATE = "server.mako"
    active = 'servers'
    expanded = True

def make_servers(global_conf):
    return ServerConfig(global_conf)
