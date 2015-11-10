from webob import exc
from akiri.framework.admin import BaseLoginApplication

from controller.profile import UserProfile
from controller.environment import Environment
from controller.palapi import CommHandlerApp
from controller.passwd import tableau_hash
from controller.system import SystemKeys
from controller.yml import YmlEntry

from .setup import AuthType
from .page import Page

class LoginApplication(BaseLoginApplication):
    """Handler for the login page.
    The page is submitted here and then redirected as necessary."""

    DEFAULT_HASH = 'de5d1b109bd9ecf5d926e0a2385d973d0d17fda2'

    def __init__(self, secret, **kwargs):
        super(LoginApplication, self).__init__(secret, **kwargs)
        self.commapp = CommHandlerApp(self)

    def __getattr__(self, name):
        if name == 'environment':
            return Environment.get()
        raise AttributeError(name)

    def authenticate(self, req, username, password, service='login'):
        envid = self.environment.envid
        entry = UserProfile.get(envid, 0) # user '0', likely 'palette'
        if entry and username == entry.name:
            # 'palette' always uses local authentication
            allow_palette_login = req.system[SystemKeys.PALETTE_LOGIN]
            if allow_palette_login:
                hashed_password = tableau_hash(password, entry.salt)
                if hashed_password == self.DEFAULT_HASH:
                    return True

            return UserProfile.verify(envid, username, password)

        # Use the configured authentication method.
        auth_type = req.system[SystemKeys.AUTHENTICATION_TYPE]
        if auth_type == AuthType.TABLEAU:
            value = YmlEntry.get(self.environment.envid,
                                 'wgserver.authenticate',
                                 default=None)
            if not value or value.lower() != 'activedirectory':
                return UserProfile.verify(envid, username, password)
            auth_type = AuthType.ACTIVE_DIRECTORY

        if auth_type == AuthType.ACTIVE_DIRECTORY:
            cmd = "ad verify " + username + " " + password
            if req.system[SystemKeys.ACTIVE_DIRECTORY_AGENT]:
                cmd = '/uuid=%s ' + cmd
            try:
                self.commapp.send_cmd(cmd, read_response=True)
            except StandardError:
                return False
            # if no exception was thrown, then authentication was successful.
            return True

        if auth_type == AuthType.LOCAL:
            return UserProfile.verify(envid, username, password)

        raise ValueError("Invalid authentication configuration: " + \
                          str(auth_type))

    def service_POST(self, req):
        """Workaround for a framework bug that returns None on failed
        authentication."""
        # FIXME: remove
        res = super(LoginApplication, self).service_POST(req)
        if res is None:
            raise exc.HTTPForbidden()
        return res


class LoginPage(Page):
    """Basic login page."""
    TEMPLATE = 'login.mako'
