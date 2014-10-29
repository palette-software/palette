from webob import exc

from controller.profile import Role
from controller.util import utc2local, DATEFMT
from controller.yml import YmlEntry, YML_LOCATION_SYSTEM_KEY

from page import PalettePage
from rest import PaletteRESTHandler

class YmlApplication(PaletteRESTHandler):
    NAME = 'yml'

    def handle(self, req):
        if req.method != 'GET':
            raise exc.HTTPBadRequest()

        last_update = None

        items = []
        entries = YmlEntry.get_all_by_envid(req.envid, order_by="key asc")
        for entry in entries:
            items.append(entry.todict())

            # since the entries list must be traversed anyway,
            # last_update can be calculated along the way.
            if last_update is None:
                last_update = entry.modification_time
            elif last_update < entry.modification_time:
                last_update = entry.modification_time

        data = {'items': items}
        if not last_update is None:
            last_update = utc2local(last_update)
            data['last-update'] = last_update.strftime(DATEFMT)

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
