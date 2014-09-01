import os

from akiri.framework.api import RESTApplication
from akiri.framework.config import store

from akiri.framework.ext.sqlalchemy import meta

from paste import fileapp
from webob import exc

from controller.profile import UserProfile
from page import PalettePage
from rest import PaletteRESTHandler

class Profile(PalettePage):
    TEMPLATE = "profile.mako"

def make_profile(global_conf):
    return Profile(global_conf)

class ProfileApplication(PaletteRESTHandler):
    # The REST application will be available at "/rest/profile"
    NAME = 'profile'

    def handle(self, req):
        if not 'REMOTE_USER' in req.environ:
            raise exc.HTTPBadRequest()

        path_info = self.base_path_info(req)
        if path_info == '':
            return self.handle_profile(req)
        raise exc.HTTPNotFound()

    def handle_profile_POST(self, req):
        raise exc.HTTPBadRequest()

    def handle_profile_GET(self, req):
        profile = req.remote_user.todict(pretty=True)

        # Add a list of roles the user has
        profile['roles'] = []
        for role in req.remote_user.roles:
            profile['roles'].append(role.name)

        return profile

    def handle_profile(self, req):
        if req.method == 'POST':
            return self.handle_profile_POST(req)
        elif req.method == 'GET':
            return self.handle_profile_GET(req)
        raise exc.HTTPMethodNotAllowed()

