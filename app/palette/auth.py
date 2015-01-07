from sqlalchemy import func

# pylint: disable=import-error,no-name-in-module
from akiri.framework.ext.sqlalchemy import meta
# pylint: enable=import-error,no-name-in-module

# FIXME: deprecate the use of 'store'
# pylint: disable=import-error,no-name-in-module
import akiri.framework.config as config
# pylint: enable=import-error,no-name-in-module

from akiri.framework.api import Authenticator
from akiri.framework.auth import AuthFilter

from controller.profile import UserProfile
from controller.domain import Domain
from controller.environment import Environment
from controller.palapi import CommHandlerApp
from controller.yml import YmlEntry

class TableauAuthenticator(Authenticator):

    def __init__(self, global_conf):
        super(TableauAuthenticator, self).__init__(global_conf)
        self.commapp = CommHandlerApp(self)

    def __getattr__(self, name):
        if name == 'domainname':
            return config.store.get('palette', 'domainname')
        if name == 'domain':
            return Domain.get_by_name(self.domainname)
        if name == 'environment':
            return Environment.get()
        raise AttributeError(name)

    def authenticate(self, username, password, service='login'):
        envid = self.environment.envid
        entry = UserProfile.get(envid, 0) # user '0', likely 'palette'
        if entry and username == entry.name:
            # 'palette' always uses local authentication
            return UserProfile.verify(envid, username, password)
        value = YmlEntry.get(self.environment.envid,
                             'wgserver.authenticate',
                             default=None)
        if not value or value.lower() != 'activedirectory':
            return UserProfile.verify(envid, username, password)
        cmd = "ad verify " + username + " " + password
        try:
            self.commapp.send_cmd(cmd, read_response=True)
        except StandardError:
            return False
        # if no exception was thrown, then authentication was successful.
        return True


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
