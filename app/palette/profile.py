from webob import exc

from .page import PalettePage
from .rest import PaletteRESTApplication

class ProfilePage(PalettePage):
    TEMPLATE = "profile.mako"

class ProfileApplication(PaletteRESTApplication):

    def service(self, req):
        if req.method == 'GET':
            return self.handle_GET(req)
        raise exc.HTTPMethodNotAllowed()

    def handle_GET(self, req):
        profile = req.remote_user.todict(pretty=True)
        profile['role'] = req.remote_user.role.name

        return profile

