from akiri.framework.api import UserInterfaceRenderer

class Organization(UserInterfaceRenderer):

    TEMPLATE = "organization.mako"
    def handle(self, req):
        return None

def make_organization(global_conf):
    return Organization(global_conf)
