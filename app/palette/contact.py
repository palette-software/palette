from page import PalettePage

class Contact(PalettePage):

    TEMPLATE = "contact.mako"
    active = None

    def handle(self, req):
        return None

def make_contact(global_conf):
    return Contact(global_conf)
