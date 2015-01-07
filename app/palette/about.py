# FIXME: deprecate the use of 'store'
# pylint: disable=import-error,no-name-in-module
import akiri.framework.config as config
# pylint: enable=import-error,no-name-in-module

from controller.domain import Domain
from page import PalettePage

try:
    # pylint: disable=no-name-in-module,import-error
    from controller.version import VERSION, DATE
    # pylint: enable=no-name-in-module,import-error
except ImportError:
    from controller.util import version, builddate
    VERSION = version()
    DATE = builddate()

class About(PalettePage):
    TEMPLATE = 'about.mako'
    active = 'about'
    expanded = True

    def __init__(self, global_conf):
        super(About, self).__init__(global_conf)
        if DATE:
            self.version = VERSION + ' - ' + DATE
        else:
            self.version = VERSION
        self.domainname = config.store.get('palette', 'domainname')
        self.license_key = None

    def render(self, req, obj=None):
        domain = Domain.get_by_name(self.domainname)
        self.license_key = domain.license_key
        return super(About, self).render(req, obj=obj)

def make_about(global_conf):
    return About(global_conf)
