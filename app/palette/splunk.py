from akiri.framework.api import UserInterfaceRenderer

class Splunk(UserInterfaceRenderer):
    TEMPLATE = "splunk.mako"
    active = 'splunk'

def make_splunk(global_conf):
    return Splunk(global_conf)
