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

    def get(self, req):
        # REST handlers don't automatically load profile objects
        user = req.environ['REMOTE_USER']
        return UserProfile.get_by_name(self.environment.envid, user)

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
        profile = self.get(req)
        if not profile:
            return {}

        self.profile = {}
        # Convert db entry into a dictionary
        for key in ['name', 'friendly_name', 'email']:
            value = getattr(profile, key)
            if value:
                self.profile[key.replace('_','-')] = value

        # Add a list of roles the user has
        self.profile['roles'] = []
        for role in profile.roles:
            self.profile['roles'].append(role.name)

        return self.profile

    def handle_profile(self, req):
        if req.method == 'POST':
            return self.handle_profile_POST(req)
        elif req.method == 'GET':
            return self.handle_profile_GET(req)
        raise exc.HTTPMethodNotAllowed()

