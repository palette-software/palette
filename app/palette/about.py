from page import PalettePage

try:
    # pylint: disable=no-name-in-module,import-error
    from controller.version import VERSION, DATE
    # pylint: enable=no-name-in-module,import-error
except ImportError:
    from controller.util import version, builddate
    VERSION = version()
    DATE = builddate()

class AboutPage(PalettePage):
    TEMPLATE = 'about.mako'
    active = 'about'
    expanded = True

    def __init__(self):
        super(AboutPage, self).__init__()
        if DATE:
            self.version = VERSION + ' - ' + DATE
        else:
            self.version = VERSION
        self.license_key = None

    def render(self, req, obj=None):
        # FIXME: make obj separate or go to REST implementation.
        self.license_key = req.palette_domain.license_key
        return super(AboutPage, self).render(req, obj=obj)

