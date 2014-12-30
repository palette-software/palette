from webob import exc

from controller.profile import Role
from controller.yml import YmlEntry
from controller.yml import YML_LOCATION_SYSTEM_KEY, YML_TIMESTAMP_SYSTEM_KEY

from .page import PalettePage
from .rest import PaletteRESTApplication

class YmlApplication(PaletteRESTApplication):
    def service(self, req):
        if req.method != 'GET':
            raise exc.HTTPBadRequest()

        entries = YmlEntry.get_all_by_envid(req.envid, order_by="key asc")

        data = {'items': [x.todict() for x in entries]}

        last_update = req.system.get(YML_TIMESTAMP_SYSTEM_KEY, default=None)
        if not last_update is None:
            data['last-update'] = last_update

        location = req.system.get(YML_LOCATION_SYSTEM_KEY, default=None)
        if not location is None:
            data['location'] = location

        return data

class YmlPage(PalettePage):
    TEMPLATE = 'yml.mako'
    active = 'yml'
    expanded = True
    required_role = Role.READONLY_ADMIN

def make_yml(global_conf):
    return YmlPage(global_conf)
