from webob import exc

from controller.profile import Role
from controller.system import SystemKeys
from controller.yml import YmlEntry

from .page import PalettePage
from .rest import PaletteRESTApplication

class YmlApplication(PaletteRESTApplication):
    def service(self, req):
        if req.method != 'GET':
            raise exc.HTTPBadRequest()

        entries = YmlEntry.get_all_by_envid(req.envid, order_by="key asc")

        data = {'items': [x.todict() for x in entries]}

        last_update = req.system[SystemKeys.YML_TIMESTAMP]
        if not last_update is None:
            data['last-update'] = last_update

        location = req.system[SystemKeys.YML_LOCATION]
        if not location is None:
            data['location'] = location

        return data

class YmlPage(PalettePage):
    TEMPLATE = 'yml.mako'
    active = 'yml'
    expanded = True
    required_role = Role.READONLY_ADMIN
