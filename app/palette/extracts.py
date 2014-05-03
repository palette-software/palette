from akiri.framework.api import UserInterfaceRenderer

class Extract(UserInterfaceRenderer):
    TEMPLATE = 'extracts.mako'
    main_active = 'extracts'

def make_extracts(global_conf):
    return Extract(global_conf)
