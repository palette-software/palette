from page import PalettePage

class Organization(PalettePage):

    TEMPLATE = "organization.mako"
    def handle(self, req):
        return None

def make_organization(global_conf):
    return Organization(global_conf)
