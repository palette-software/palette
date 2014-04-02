from akiri.framework.api import UserInterfaceRenderer

class Profile(UserInterfaceRenderer):

    TEMPLATE = "profile.mako"
    def handle(self, req):
        return None

def make_profile(global_conf):
    return Profile(global_conf)
