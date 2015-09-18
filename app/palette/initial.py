"""The initial setup page - as opposed to the configuration setup page.
The handlers for this page have no access control until after setup is
complete, and are hence 'open'
"""
# pylint: enable=missing-docstring,relative-import

from webob import exc, Response
from paste.auth.auth_tkt import AuthTicket

from akiri.framework import GenericWSGIApplication
import akiri.framework.sqlalchemy as meta

from controller.licensing import licensing_send, licensing_info
from controller.licensing import LicenseException
from controller.profile import UserProfile
from controller.system import SystemKeys

from .about import display_version
from .page import Page
from .setup import _SetupApplication
from .rest import required_parameters

class InitialSetupPage(Page):
    """ The first setup page shown with new servers. """
    TEMPLATE = "initial.mako"

class InitialSetupApplication(GenericWSGIApplication):
    """REST-like handler that responds only to the initial setup AJAX call."""

    def __init__(self, secret):
        self.setup = _SetupApplication()
        self.secret = secret
        super(InitialSetupApplication, self).__init__()

    def service_GET(self, req):
        """GET request: used to pre-populate the initial setup page."""
        # This is required in order to bypass the required role.
        entry = UserProfile.get(req.envid, 0) # user '0', likely 'palette'
        if entry.hashed_password:
            # Configuration was already done
            raise exc.HTTPServiceUnavailable()
        data = self.setup.service_GET(req)
        data['license-key'] = req.palette_domain.license_key
        data['version'] = display_version()
        proxy_https = req.system[SystemKeys.PROXY_HTTPS]
        if proxy_https:
            data['proxy-https'] = proxy_https
        return data

    def _set_license_key(self, req):
        """Set the license key in the domain table."""
        license_key = req.params_get('license-key').strip()

        info = licensing_info(req.palette_domain, req.envid, req.system)
        info['license-key'] = license_key

        data = licensing_send('/api/trial-start', info, req.system)

        req.palette_domain.license_key = license_key
        if 'trial' in data:
            req.palette_domain.trial = data['trial']
        if 'expiration-time' in data:
            req.palette_domain.expiration_time = data['expiration-time']
        if 'id' in data:
            req.palette_domain.domainid = int(data['id'])

        meta.Session.commit()

    # FIXME: this should be one big database transaction.
    # The new framework session middleware will do this implicitly.
    def service_save(self, req):
        """Handler for the 'Save Settings' button at the bottom of the page."""
        entry = UserProfile.get(req.envid, 0) # user '0', likely 'palette'
        if entry.hashed_password:
            # Configuration was already done
            raise exc.HTTPServiceUnavailable()

        if req.platform.product != req.platform.PRODUCT_PRO:
            try:
                self._set_license_key(req)
            except LicenseException, ex:
                if ex.status == 404:
                    reason = 'Invalid license key'
                else:
                    reason = ex.reason
                return {'status': 'FAILED', 'error': reason}
            self.setup.url.service_POST(req)
            self.setup.mail.service_POST(req)

        self.setup.admin.service_POST(req)
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

    @required_parameters('value')
    def service_proxy(self, req):
        """Save a proxy configuration value to the system table."""
        value = req.params['value']
        if value:
            req.system[SystemKeys.PROXY_HTTPS] = value
        else:
            del req.system[SystemKeys.PROXY_HTTPS]
        meta.commit()
        return {'status': 'OK'}

    @required_parameters('action')
    def service_POST(self, req):
        """POST handler for all page buttons."""
        action = req.params['action']
        if action == 'save':
            return self.service_save(req)
        if action == 'test':
            return self.setup.mail.service_POST(req, initial_page=True)
        if action == 'proxy':
            return self.service_proxy(req)
        raise exc.HTTPBadRequest("Invalid 'action'")


class InitialMiddleware(GenericWSGIApplication):
    """ Test whether the system has been initially setup."""

    def service_GET(self, req):
        """Redirect all pages to /setup if the system hasn't been setup.
        The setup status is determined by whether or not the palette user
        has a password or not.
        """
        if 'REMOTE_USER' in req.environ:
            # If REMOTE_USER is set - presumably from auth_tkt,
            # then setup has already been done.
            return

        entry = UserProfile.get(req.envid, 0) # user '0', likely 'palette'
        if not entry.hashed_password:
            raise exc.HTTPTemporaryRedirect(location='/setup')
