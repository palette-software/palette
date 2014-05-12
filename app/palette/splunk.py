from configure import ConfigureRenderer

class Splunk(ConfigureRenderer):
    TEMPLATE = "splunk.mako"
    configure_active = 'splunk'

def make_splunk(global_conf):
    return Splunk(global_conf)
