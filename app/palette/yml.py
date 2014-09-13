from webob import exc

# pylint: disable=import-error,no-name-in-module
from akiri.framework.ext.sqlalchemy import meta
# pylint: enable=import-error,no-name-in-module

from controller.agentinfo import AgentYmlEntry
from controller.profile import Role

from page import PalettePage
from rest import PaletteRESTHandler

class YMLApplication(PaletteRESTHandler):
    NAME = 'yml'

    def handle(self, req):
        if req.method != 'GET':
            raise exc.HTTPBadRequest()

        # FIXME: filter by agentid of the primary.
        query = meta.Session.query(AgentYmlEntry).\
            order_by(AgentYmlEntry.key.asc())

        return {'items': [x.todict() for x in query.all()]}

class YML(PalettePage):
    TEMPLATE = 'yml.mako'
    active = 'yml'
    expanded = True
    required_role = Role.READONLY_ADMIN

def make_yml(global_conf):
    return YML(global_conf)
