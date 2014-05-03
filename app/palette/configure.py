from akiri.framework.api import UserInterfaceRenderer

class ConfigureRenderer(UserInterfaceRenderer):
    main_active = 'configure'

    def handle(self, req):
        return None
