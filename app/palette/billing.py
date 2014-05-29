from page import PalettePage

class Billing(PalettePage):
    TEMPLATE = "billing.mako"
    active = 'billing'

def make_billing(global_conf):
    return Billing(global_conf)
