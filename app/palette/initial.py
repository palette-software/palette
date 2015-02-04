from webob import exc

from akiri.framework import GenericWSGIApplication

# pylint: disable=import-error,no-name-in-module
from akiri.framework.ext.sqlalchemy import meta
# pylint: enable=import-error,no-name-in-module

from controller.profile import UserProfile

from .setup import _SetupApplication
from .rest import required_parameters

class OpenApplication(GenericWSGIApplication):
    """REST-like handler that responds only to the initial setup AJAX call."""

    def __init__(self):
        self.setup = _SetupApplication()
        super(OpenApplication, self).__init__()

    def service_GET(self, req):
        # This is required in order to bypass the required role.
        return self.setup.service_GET(req)

    def _set_license_key(self, req):
        license_key = req.params_get('license-key')
        req.palette_domain.license_key = license_key
        meta.Session.commit()

    # FIXME (later): this should be one big database transaction.
    # The new framework session middleware will do this implicitly.
    @required_parameters('license-key')
    def service_save(self, req):
        # FIXME: test for null password in palette.
        self._set_license_key(req)
        self.setup.admin.service_POST(req)
        self.setup.mail.service_POST(req)
        self.setup.ssl.service_POST(req)
        self.setup.url.service_POST(req)
        # FIXME: login the user.
        return {}

    @required_parameters('action')
    def service_POST(self, req):
        action = req.params['action']
        print 'init req:', req.POST, 'action:', action
        if action == 'save':
            return self.service_save(req)
        if action == 'test':
            return self.setup.mail.service_POST(req, initial_page=True)
        raise exc.HTTPBadRequest(req)


def make_open(global_conf):
    # pylint: disable=unused-argument
    return OpenApplication()

class InitialApp(GenericWSGIApplication):
    """ Test whether the system has been initially setup."""

    def service_GET(self, req):
        if 'REMOTE_USER' in req.environ:
            # If REMOTE_USER is set - presumably from auth_tkt,
            # then setup has already been done.
            return None

        entry = UserProfile.get(req.envid, 0) # user '0', likely 'palette'
        if not entry.hashed_password:
            raise exc.HTTPTemporaryRedirect(location='/setup')
        return None

def make_initial_filter(app, global_conf):
    # pylint: disable=unused-argument
    return InitialApp(app)
