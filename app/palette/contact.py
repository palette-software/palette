from akiri.framework.api import UserInterfaceRenderer

class Contact(UserInterfaceRenderer):

    TEMPLATE = "contact.mako"
    def handle(self, req):
        return None

def make_contact(global_conf):
    return Contact(global_conf)