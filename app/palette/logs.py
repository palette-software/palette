from akiri.framework.api import UserInterfaceRenderer

class Log(UserInterfaceRenderer):
    TEMPLATE = 'logs.mako'
    active = 'logs'

def make_logs(global_conf):
    return Log(global_conf)
