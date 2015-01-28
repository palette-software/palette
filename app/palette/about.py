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
        self.license_key = None

    def render(self, req, obj=None):
        self.license_key = req.palette_domain.license_key
        return super(About, self).render(req, obj=obj)

def make_about(global_conf):
    return About(global_conf)
