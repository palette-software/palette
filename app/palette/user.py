from akiri.framework.api import UserInterfaceRenderer

class UserConfig(UserInterfaceRenderer):
    TEMPLATE = "user.mako"
    active = 'users'

def make_users(global_conf):
    return UserConfig(global_conf)
