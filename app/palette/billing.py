from akiri.framework.api import UserInterfaceRenderer

class Billing(UserInterfaceRenderer):
    TEMPLATE = "billing.mako"
    active = 'billing'

def make_billing(global_conf):
    return Billing(global_conf)
