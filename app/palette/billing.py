from akiri.framework.api import UserInterfaceRenderer

class Billing(UserInterfaceRenderer):

    TEMPLATE = "billing.mako"
    def handle(self, req):
        return None

def make_billing(global_conf):
    return Billing(global_conf)
