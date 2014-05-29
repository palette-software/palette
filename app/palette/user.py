from page import PalettePage

class UserConfig(PalettePage):
    TEMPLATE = "user.mako"
    active = 'users'
    expanded = True

def make_users(global_conf):
    return UserConfig(global_conf)
