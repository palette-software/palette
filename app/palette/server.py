from akiri.framework.api import UserInterfaceRenderer

class ServerConfig(UserInterfaceRenderer):
    TEMPLATE = "server.mako"
    active = 'servers'

def make_servers(global_conf):
    return ServerConfig(global_conf)
