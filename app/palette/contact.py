from akiri.framework.api import UserInterfaceRenderer

class Contact(UserInterfaceRenderer):

    TEMPLATE = "contact.mako"
    main_active = None

    def handle(self, req):
        return None

def make_contact(global_conf):
    return Contact(global_conf)
