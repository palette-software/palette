from webob import exc, Response
from paste.auth.auth_tkt import AuthTicket

from akiri.framework import GenericWSGIApplication

# pylint: disable=import-error,no-name-in-module
from akiri.framework.ext.sqlalchemy import meta
# pylint: enable=import-error,no-name-in-module

from controller.profile import UserProfile

from .setup import _SetupApplication
from .rest import required_parameters

class OpenApplication(GenericWSGIApplication):
    """REST-like handler that responds only to the initial setup AJAX call."""

    def __init__(self, secret):
        self.setup = _SetupApplication()
        self.secret = secret
        super(OpenApplication, self).__init__()

    def service_GET(self, req):
        # This is required in order to bypass the required role.
        entry = UserProfile.get(req.envid, 0) # user '0', likely 'palette'
        if entry.hashed_password:
            # Configuration was already done
            raise exc.HTTPServiceUnavailable()
        return self.setup.service_GET(req)

    def _set_license_key(self, req):
        license_key = req.params_get('license-key')
        req.palette_domain.license_key = license_key
        meta.Session.commit()

    # FIXME (later): this should be one big database transaction.
    # The new framework session middleware will do this implicitly.
    @required_parameters('license-key')
    def service_save(self, req):
        entry = UserProfile.get(req.envid, 0) # user '0', likely 'palette'
        if entry.hashed_password:
            # Configuration was already done
            raise exc.HTTPServiceUnavailable()
        self._set_license_key(req)
        self.setup.admin.service_POST(req)
        self.setup.mail.service_POST(req)
        self.setup.ssl.service_POST(req)
        self.setup.url.service_POST(req)
        self.setup.tableau_url.service_POST(req)
        self.setup.timezone.service_POST(req)

        res = Response()
        tkt = AuthTicket(self.secret, entry.name, req.environ['REMOTE_ADDR'])
        # FIXME (later): make configurable.
        res.set_cookie('auth_tkt', tkt.cookie_value(),
                       max_age=2592000, path='/')
        res.content_type = 'application/json'
        res.body = '{}\n'
        return res

    @required_parameters('action')
    def service_POST(self, req):
        action = req.params['action']
        if action == 'save':
            return self.service_save(req)
        if action == 'test':
            return self.setup.mail.service_POST(req, initial_page=True)
        raise exc.HTTPBadRequest(req)


def make_open(global_conf):
    # pylint: disable=unused-argument
    return OpenApplication(global_conf['shared'])

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
