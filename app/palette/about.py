from page import PalettePage

try:
    from controller.version import VERSION, DATE
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

def make_about(global_conf):
    return About(global_conf)
