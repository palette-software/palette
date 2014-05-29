from page import PalettePage

class ServerConfig(PalettePage):
    TEMPLATE = "server.mako"
    active = 'servers'
    expanded = True

def make_servers(global_conf):
    return ServerConfig(global_conf)
