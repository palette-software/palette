from configure import ConfigureRenderer

class Billing(ConfigureRenderer):
    TEMPLATE = "billing.mako"

    def __init__(self, global_conf):
        super(Billing, self).__init__(global_conf)
        self.configure_active = 'billing'

def make_billing(global_conf):
    return Billing(global_conf)
