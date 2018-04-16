# Copyright (c) Akiri Solutions, Inc.  All Rights Reserved.
"""Helper functionality for administrative tasks e.g. login and logout."""
from webob import exc
from paste.auth.auth_tkt import AuthTicket

from . import GenericWSGIApplication
from .util import required_parameters

__HAVE_PAM = False
try:
    import PAM
    __HAVE_PAM = True
except ImportError:
    pass

class BaseLoginApplication(GenericWSGIApplication):
    """Simple login handler - expects a POST with 'username' and 'password'
    This class needs to be overridden to be used, otherwise always fails."""
    # pylint: disable = too-many-instance-attributes

    def __init__(self, secret, allow_root=False,
                 max_age=None, path='/', domain=None, secure=False,
                 httponly=False, comment=None, overwrite=False):
        # pylint: disable = too-many-arguments
        super(BaseLoginApplication, self).__init__()
        self.secret = secret
        self.allow_root = allow_root
        self.max_age = max_age
        self.path = path
        self.domain = domain
        self.secure = secure
        self.httponly = httponly
        self.comment = comment
        self.overwrite = overwrite

    def authenticate(self, req, username, password, service='login'):
        """Override this for particular types of authentication."""
        # pylint: disable=unused-argument
        # pylint: disable=no-self-use
        return False

    def forbidden(self, req):
        """Handler for when authentication fails."""
        # pylint: disable=unused-argument
        # pylint: disable=no-self-use
        return exc.HTTPForbidden()

    @required_parameters('username', 'password')
    def service_POST(self, req):
        """Handle POST"""
        username = req.params['username']
        password = req.params['password']

        location = req.params_get('location', default=None)
        if not location:
            location = '/'
        service = req.params_get('service', default=None)
        if not service:
            service = 'login'

        # Don't provide additional information, just normal auth failure.
        if username == 'root' and not self.allow_root:
            return self.forbidden(req)

        if not self.authenticate(req, username, password, service=service):
            return self.forbidden(req)

        tkt = AuthTicket(self.secret, username, req.environ['REMOTE_ADDR'])

        # This form must redirect in order for Chrome to handle
        # saved/remembered passwords correctly.

        # '302 Found' must be used instead of the '307 Temporary Redirect'
        # to prevent Firefox from displaying a popup about sending form data.
        res = exc.HTTPFound(location=location)

        res.set_cookie('auth_tkt', tkt.cookie_value(),
                       max_age=self.max_age,
                       path=self.path,
                       domain=self.domain,
                       secure=self.secure,
                       httponly=self.httponly,
                       comment=self.comment,
                       overwrite=self.overwrite)
        return res


class LogoutApplication(GenericWSGIApplication):
    """Simple logout handler"""

    def __init__(self, redirect, cookie_name='auth_tkt'):
        super(LogoutApplication, self).__init__()
        self.redirect = redirect
        self.cookie_name = cookie_name

    def service_GET(self, req):
        """Handle GET"""
        # pylint: disable=unused-argument
        res = exc.HTTPTemporaryRedirect(location=self.redirect)
        res.delete_cookie(self.cookie_name)
        return res


if __HAVE_PAM:
    class PAMLoginApplication(BaseLoginApplication):
        """Authenticate again normal unix credentials."""
        def authenticate(self, req, username, password, service='login'):
            def _pam_conv(auth, query_list, userdata):
                """internal helper function"""
                # pylint: disable=unused-argument
                resp = []
                resp.append((password, 0))
                return resp
            service = 'passwd'

            auth = PAM.pam()
            auth.start(service)
            auth.set_item(PAM.PAM_USER, username)
            auth.set_item(PAM.PAM_CONV, _pam_conv)
            try:
                auth.authenticate()
                auth.acct_mgmt()
            except PAM.error:
                # FIXME: logging
                return False
            return True

class TokenLoginApplication(BaseLoginApplication):
    """Simple token lookup authentication (testing/examples only)"""
    def authenticate(self, req, username, password, service='login'):
        return password == self.secret
