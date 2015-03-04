from webob import exc
from akiri.framework.admin import BaseLoginApplication

from controller.profile import UserProfile
from controller.environment import Environment
from controller.palapi import CommHandlerApp
from controller.general import SystemConfig
from controller.system import SystemEntry
from controller.yml import YmlEntry

from .setup import AuthType
from .page import Page

class LoginApplication(BaseLoginApplication):
    """Handler for the login page.
    The page is submitted here and then redirected as necessary."""

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
            return UserProfile.verify(envid, username, password)

        # Use the configured authentication method.
        auth_entry = SystemEntry.get_by_key(envid,
                                           SystemConfig.AUTHENTICATION_TYPE,
                                           default=None)

        if auth_entry is None:
            auth_type = AuthType.TABLEAU
        else:
            auth_type = int(auth_entry.value)

        if auth_type == AuthType.TABLEAU:
            value = YmlEntry.get(self.environment.envid,
                                 'wgserver.authenticate',
                                 default=None)
            if not value or value.lower() != 'activedirectory':
                return UserProfile.verify(envid, username, password)
            auth_type = AuthType.ACTIVE_DIRECTORY

        if auth_type == AuthType.ACTIVE_DIRECTORY:
            cmd = "ad verify " + username + " " + password
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
