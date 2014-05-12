from webob import exc

from akiri.framework.api import RESTApplication

from controller.meta import Session
from controller.agentinfo import AgentYmlEntry

from configure import ConfigureRenderer

class YMLApplication(RESTApplication):
    NAME='yml'

    def handle(self, req):
        if req.method != 'GET':
            raise exc.HTTPBadRequest();
        
        query = Session.query(AgentYmlEntry).\
            order_by(AgentYmlEntry.key.asc())

        return {'items': [x.todict() for x in query.all()]}

class YML(ConfigureRenderer):
    TEMPLATE = 'yml.mako'
    configure_active = 'yml'

def make_yml(global_conf):
    return YML(global_conf)
