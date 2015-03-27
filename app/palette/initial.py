from webob import exc, Response
from paste.auth.auth_tkt import AuthTicket

from akiri.framework import GenericWSGIApplication
import akiri.framework.sqlalchemy as meta

from controller.profile import UserProfile
from controller.licensing import licensing_send, licensing_info
from controller.licensing import LicenseException

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
        data = self.setup.service_GET(req)
        data['license-key'] = req.palette_domain.license_key
        return data

    def _set_license_key(self, req):
        license_key = req.params_get('license-key').strip()

        info = licensing_info(req.palette_domain, req.envid)
        info['license-key'] = license_key

        data = licensing_send('/api/trial-start', info)

        req.palette_domain.license_key = license_key
        if 'trial' in data:
            req.palette_domain.trial = data['trial']
        if 'expiration-time' in data:
            req.palette_domain.expiration_time = data['expiration-time']
        if 'id' in data:
            req.palette_domain.domainid = int(data['id'])

        meta.Session.commit()

    # FIXME (later): this should be one big database transaction.
    # The new framework session middleware will do this implicitly.
    @required_parameters('license-key')
    def service_save(self, req):
        entry = UserProfile.get(req.envid, 0) # user '0', likely 'palette'
        if entry.hashed_password:
            # Configuration was already done
            raise exc.HTTPServiceUnavailable()

        try:
            self._set_license_key(req)
        except LicenseException, ex:
            if ex.status == 404:
                reason = 'Invalid license key'
            else:
                reason = ex.reason
            return {'status': 'FAILED', 'error': reason}
        self.setup.admin.service_POST(req)
        self.setup.readonly.service_POST(req)
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
        res.body = '{"status":"OK"}\n'
        return res

    @required_parameters('action')
    def service_POST(self, req):
        action = req.params['action']
        if action == 'save':
            return self.service_save(req)
        if action == 'test':
            return self.setup.mail.service_POST(req, initial_page=True)
        raise exc.HTTPBadRequest(req)


class InitialMiddleware(GenericWSGIApplication):
    """ Test whether the system has been initially setup."""

    def service_GET(self, req):
        if 'REMOTE_USER' in req.environ:
            # If REMOTE_USER is set - presumably from auth_tkt,
            # then setup has already been done.
            return

        entry = UserProfile.get(req.envid, 0) # user '0', likely 'palette'
        if not entry.hashed_password:
            raise exc.HTTPTemporaryRedirect(location='/setup')
