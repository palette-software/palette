from akiri.framework.api import UserInterfaceRenderer

class ConfigureRenderer(UserInterfaceRenderer):

    def __init__(self, global_conf):
        super(ConfigureRenderer, self).__init__(global_conf)
        self.main_active = 'configure'

    def handle(self, req):
        return None
