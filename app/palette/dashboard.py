from collections import OrderedDict

from .page import PalettePage
from .rest import PaletteRESTApplication
from .option import DictOption

class DashboardType(DictOption):
    """Representation of the 'dashboard' dropdown."""
    NAME = 'dashboard-type'

    def __init__(self):
        options = OrderedDict({})
        valueid = 'Dashboard1'
        options[valueid] = 'Dashboard 1 (Default)'
        for i in range(2, 10):
            options['Dashboard'+str(i)] = 'Dashboard '+str(i)
        super(DashboardType, self).__init__(self.NAME, valueid, options)

class DashboardPage(PalettePage):
    TEMPLATE = 'dashboard.mako'
    active = 'home'


class DashboardApplication(PaletteRESTApplication):

    def service_GET(self, req):
        # pylint: disable=unused-argument
        return {'config': [DashboardType().default()]}

