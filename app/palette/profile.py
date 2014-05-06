import os

from akiri.framework.api import RESTApplication
from akiri.framework.config import store

from paste import fileapp
from webob import exc

from controller.meta import Session
from controller.profile import UserProfile

from configure import ConfigureRenderer

class Profile(ConfigureRenderer):
    TEMPLATE = "profile.mako"
    configure_active = 'profile'

def make_profile(global_conf):
    return Profile(global_conf)

class ProfileApplication(RESTApplication):
    # The REST application will be available at "/rest/profile"
    NAME = 'profile'

    def handle(self, req):
        if not 'REMOTE_USER' in req.environ:
            raise exc.HTTPBadRequest()

        if req.environ['PATH_INFO'] == '/profile':
            return self.handle_profile(req)
        raise exc.HTTPBadRequest()

    def handle_profile_POST(self, req):
        raise exc.HTTPBadRequest()

    def handle_profile_GET(self, req):
        user_name = req.environ['REMOTE_USER']
        user_profile = UserProfile.get_by_name(user_name)

        if not user_profile:
            return {}

        self.profile = {}
        # Convert db entry into a dictionary
        for key in ['userid', 'name', 'first_name', 'last_name', 'email',
                                        'tableau_username', 'gmt']:
            self.profile[key] = getattr(user_profile, key)

        # Add a list of roles the user has
        self.profile['roles'] = []
        for role in user_profile.roles:
            self.profile['roles'].append(role.name)

        return self.profile

    def handle_profile(self, req):
        if req.method == 'POST':
            return self.handle_profile_POST(req)
        elif req.method == 'GET':
            return self.handle_profile_GET(req)
        raise exc.HTTPBadRequest()
