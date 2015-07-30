from webob import exc

from controller.profile import Role

from page import PalettePage
from .rest import required_parameters, required_role, PaletteRESTApplication

from controller.general import SystemConfig
JSON_KEY = 'enable-support'

try:
    # pylint: disable=no-name-in-module,import-error
    from controller.version import VERSION, DATE
    # pylint: enable=no-name-in-module,import-error
except ImportError:
    from controller.util import version, builddate
    VERSION = version()
    DATE = builddate()

def display_version():
    if DATE:
        return VERSION + ' - ' + DATE
    return VERSION

class AboutPage(PalettePage):
    TEMPLATE = 'about.mako'
    active = 'about'
    expanded = True

    def __init__(self):
        super(AboutPage, self).__init__()
        self.version = display_version()
        self.license_key = None

    def render(self, req, obj=None):
        # FIXME: make obj separate or go to REST implementation.
        self.license_key = req.palette_domain.license_key
        return super(AboutPage, self).render(req, obj=obj)


class AboutApplication(PaletteRESTApplication):

    def service_GET(self, req):
        enabled = req.system.getbool(SystemConfig.SUPPORT_ENABLED, default=True,
                                    cleanup=True)
        if req.path_info.endswith('/support'):
            return {JSON_KEY: enabled}

        return {'licence-key': req.palette_domain.license_key,
                'version': display_version(),
                JSON_KEY: enabled}

    @required_role(Role.MANAGER_ADMIN)
    @required_parameters('value')
    def service_POST(self, req):
        if not req.path_info.endswith('/support'):
            raise exc.HTTPMethodNotAllowed()
        value = req.POST['value'].lower()
        if value == 'false':
            self.commapp.send_cmd("support off", req=req, read_response=False)
        else:
            self.commapp.send_cmd("support on", req=req, read_response=False)
            value = 'true'
        return {'value': value}
