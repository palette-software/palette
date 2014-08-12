import json
from sqlalchemy import func
from akiri.framework.ext.sqlalchemy import meta

from akiri.framework.api import Authenticator
from akiri.framework.auth import AuthFilter
from akiri.framework.config import store

from controller.agentinfo import AgentYmlEntry
from controller.profile import UserProfile

from controller.domain import Domain
from rest import Telnet

class TableauAuthenticator(Authenticator):

    def __init__(self, global_conf):
        super(TableauAuthenticator, self).__init__(global_conf)
        self.telnet = Telnet(self)

    def __getattr__(self, name):
        if name == 'domainname':
            return store.get('palette', 'domainname')
        if name == 'domain':
            return Domain.get_by_name(self.domainname)

    # FIXME: this is a hack since there isn't currently any
    # concept of agent, environment or domain during login.
    def yml(self, key):
        entry = meta.Session.query(AgentYmlEntry).\
            filter(AgentYmlEntry.key == key).first()
        return entry and entry.value or None
    
    def authenticate(self, username, password, service='login'):
        entry = UserProfile.get(0) # user '0', likely 'palette'
        if entry and username == entry.name:
            # 'palette' always uses local authentication
            return UserProfile.verify(username, password)
        value = self.yml('wgserver.authenticate')
        if not value or value.lower() != 'activedirectory':
            return UserProfile.verify(username, password)
        cmd = "ad verify " + username + " " + password
        data = self.telnet.send_cmd(cmd, sync=True)
        d = json.loads(data)
        # FIXME: create a util function for this.
        return (('status' in d) and (d['status'].upper() == 'OK'))


class TableauAuthFilter(AuthFilter):

    def __call__(self, environ, start_response):
        if 'REMOTE_USER' in environ:
            user = UserProfile.get_by_name(environ['REMOTE_USER'])
            user.timestamp = func.current_timestamp()
            meta.Session.commit()
            environ['REMOTE_USER'] = user
        return super(TableauAuthFilter, self).__call__(environ, start_response)
