from webob import exc

from akiri.framework.api import RESTApplication

from akiri.framework.ext.sqlalchemy import meta

from controller.agentinfo import AgentYmlEntry

from akiri.framework.api import UserInterfaceRenderer

class YMLApplication(RESTApplication):
    NAME='yml'

    def handle(self, req):
        if req.method != 'GET':
            raise exc.HTTPBadRequest();
        
        query = meta.Session.query(AgentYmlEntry).\
            order_by(AgentYmlEntry.key.asc())

        return {'items': [x.todict() for x in query.all()]}

class YML(UserInterfaceRenderer):
    TEMPLATE = 'yml.mako'
    active = 'yml'

def make_yml(global_conf):
    return YML(global_conf)
