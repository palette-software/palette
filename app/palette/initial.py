from webob import exc

from akiri.framework import GenericWSGIApplication
from akiri.framework.ext.sqlalchemy import meta

from controller.profile import UserProfile
from controller.domain import Domain

from .setup import _SetupApplication
from .routing import req_getattr
from .rest import required_parameters

class OpenApplication(GenericWSGIApplication):
    """REST-like handler that responds only to the initial setup AJAX call."""

    def __init__(self):
        self.setup = _SetupApplication()

    # FIXME: remove this call.
    def service(self, req):
        # FIXME: don't override the existing remote_user, instead create
        # a different member like 'remote_user_profile'.
        req.getattr = req_getattr
        return super(OpenApplication, self).service(req)

    def service_GET(self, req):
        # This is required in order to bypass the required role.
        return self.setup.service_GET(req)

    def _set_license_key(self, license_key):
        domain = Domain.getone()
        domain.license_key = license_key
        meta.Session.commit()

    # FIXME (later): this should be one big database transaction.
    # The new framework session middleware will do this implicitly.
    @required_parameters('license-key')
    def service_POST(self, req):
        # FIXME: test for null password in palette.
        print 'setup:', req
        self._set_license_key(req.params_get('license-key'))
        self.setup.admin.service_POST(req)
        print 'before mail'
        self.setup.mail.service_POST(req)
        print 'after mail'
        self.setup.ssl.service_POST(req)
        self.setup.url.service_POST(req)
        print 'and done'
        # FIXME: login the user.
        return {}


def make_open(global_conf):
    return OpenApplication()

class SetupTestApp(GenericWSGIApplication):
    """ WSGI Middleware to test whether the system has been initially setup."""

    def service_GET(self, req):
        if 'REMOTE_USER' in req.environ:
            # If REMOTE_USER is set - presumably from auth_tkt,
            # then setup has already been done.
            return None

        # FIXME: redundant
        from .routing import req_getattr
        req.getattr = req_getattr

        entry = UserProfile.get(req.envid, 0) # user '0', likely 'palette'
        if not entry.hashed_password:
            raise exc.HTTPTemporaryRedirect(location='/setup')
        return None

def make_setup_test(app, global_conf):
    # pylint: disable=unused-argument
    return SetupTestApp(app)
