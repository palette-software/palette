from akiri.framework.api import UserInterfaceRenderer
from akiri.framework.api import RESTApplication

from webob import exc

from controller.profile import UserProfile

class Profile(UserInterfaceRenderer):

    TEMPLATE = "profile.mako"
    def handle(self, req):
        return None

def make_profile(global_conf):
    return Profile(global_conf)

class ProfileApplication(RESTApplication):
    # The REST application will be available at "/rest/profile":
    NAME = 'profile'

    def handle_POST(self, req):
        raise exc.HTTPBadRequest()

    def handle_GET(self, req):
        if not 'name' in req.GET:
            raise exc.HTTPBadRequest()
        user_profile = UserProfile.get_by_name(req.GET['name'])

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

    def handle(self, req):
        if req.method == 'POST':
            return self.handle_POST(req)
        elif req.method == 'GET':
            return self.handle_GET(req)
        raise exc.HTTPBadRequest()
