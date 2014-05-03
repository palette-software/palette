from configure import ConfigureRenderer

class Billing(ConfigureRenderer):
    TEMPLATE = "billing.mako"
    configure_active = 'billing'

def make_billing(global_conf):
    return Billing(global_conf)
