from page import PalettePage

class Log(PalettePage):
    TEMPLATE = 'logs.mako'
    active = 'logs'

def make_logs(global_conf):
    return Log(global_conf)
