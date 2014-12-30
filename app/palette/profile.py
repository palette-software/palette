from webob import exc

from .page import PalettePage
from .rest import PaletteRESTApplication

class Profile(PalettePage):
    TEMPLATE = "profile.mako"

def make_profile(global_conf):
    return Profile(global_conf)

class ProfileApplication(PaletteRESTApplication):

    def service(self, req):
        if req.method == 'GET':
            return self.handle_GET(req)
        raise exc.HTTPMethodNotAllowed()

    def handle_GET(self, req):
        profile = req.remote_user.todict(pretty=True)

        # Add a list of roles the user has
        profile['roles'] = []
        for role in req.remote_user.roles:
            profile['roles'].append(role.name)

        return profile

