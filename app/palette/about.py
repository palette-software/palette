from webob import exc

from controller.profile import Role
from controller.general import SystemConfig
from controller.util import extend

from page import PalettePage
from .rest import required_parameters, required_role, PaletteRESTApplication

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


class AboutApplication(PaletteRESTApplication):
    """REST Application for the 'about' page."""
    def __init__(self):
        super(AboutApplication, self).__init__()
        self.support = SupportApplication()
        self.auto_update = AutoUpdateApplication()

    def service_GET(self, req):
        data = {'license-key': req.palette_domain.license_key,
                'version': display_version()}
        extend(data, self.support.service_GET(req))
        extend(data, self.auto_update.service_GET(req))
        return data


class SupportApplication(PaletteRESTApplication):
    """Handle enable/disable of the Support Tunnel"""
    JSON_KEY = 'enable-support'

    def service_GET(self, req):
        enabled = req.system.getyesno(SystemConfig.SUPPORT_ENABLED,
                                     default=True,
                                     cleanup=True)
        return {self.JSON_KEY: enabled}

    @required_role(Role.MANAGER_ADMIN)
    @required_parameters('value')
    def service_POST(self, req):
        value = req.POST['value'].lower()
        if value == 'false':
            self.commapp.send_cmd("support off", req=req, read_response=False)
        else:
            self.commapp.send_cmd("support on", req=req, read_response=False)
            value = 'true'
        return {'value': value}


class AutoUpdateApplication(PaletteRESTApplication):
    """Configure automatic updates."""
    JSON_KEY = 'enable-updates'

    def service_GET(self, req):
        enabled = req.system.getyesno(SystemConfig.AUTO_UPDATE_ENABLED,
                                     default=True,
                                     cleanup=True)
        return {self.JSON_KEY: enabled}

    @required_role(Role.MANAGER_ADMIN)
    @required_parameters('value')
    def service_POST(self, req):
        value = req.POST['value'].lower()
        if value == 'false':
            req.system.save(SystemConfig.AUTO_UPDATE_ENABLED, 'no')
        else:
            req.system.save(SystemConfig.AUTO_UPDATE_ENABLED, 'yes')
            value = 'true'
        return {'value': value}
