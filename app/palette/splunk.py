from page import PalettePage

class Splunk(PalettePage):
    TEMPLATE = "splunk.mako"
    active = 'splunk'
    integration = True

def make_splunk(global_conf):
    return Splunk(global_conf)
