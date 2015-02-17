from sqlalchemy import func

import akiri.framework.sqlalchemy as meta

from akiri.framework.api import Authenticator
from akiri.framework.auth import AuthFilter

from controller.profile import UserProfile
from controller.environment import Environment
from controller.palapi import CommHandlerApp
from controller.general import SystemConfig
from controller.system import SystemEntry
from controller.yml import YmlEntry

from setup import AuthType

class TableauAuthenticator(Authenticator):

    def __init__(self, global_conf):
        super(TableauAuthenticator, self).__init__(global_conf)
        self.commapp = CommHandlerApp(self)

    def __getattr__(self, name):
        if name == 'environment':
            return Environment.get()
        raise AttributeError(name)

    def authenticate(self, username, password, service='login'):
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


class TableauAuthFilter(AuthFilter):

    def __call__(self, environ, start_response):
        if not hasattr(self, 'envid'):
            # pylint: disable=attribute-defined-outside-init
            self.envid = Environment.get().envid
        if 'REMOTE_USER' in environ:
            user = UserProfile.get_by_name(self.envid, environ['REMOTE_USER'])
            if user:
                user.timestamp = func.current_timestamp()
                meta.Session.commit()
                environ['REMOTE_USER'] = user
            else:
                del environ['REMOTE_USER']
        return super(TableauAuthFilter, self).__call__(environ, start_response)
