from datetime import datetime
from sqlalchemy import not_, func

import akiri.framework.sqlalchemy as meta

from manager import Manager, synchronized
from event_control import EventControl
from profile import UserProfile, Publisher, License
from util import odbc2dt, DATEFMT, success, failed

AUTH_TIMESTAMP_SYSTEM_KEY = 'auth-timestamp'

# FIXME: use the ODBC class here instead.
class AuthManager(Manager):

    # build a cache of the Tableau 'users' table.
    def load_users(self, agent):
        stmt = \
            'SELECT system_user_id, login_at, admin_level,' +\
            ' licensing_role_id, publisher_tristate ' +\
            'FROM users'

        data = agent.odbc.execute(stmt)
        if 'error' in data or not '' in data:
            return {}

        cache = {}
        for row in data['']:
            sysid = int(row[0])
            login_at = odbc2dt(row[1])
            admin_level = (row[2] is None) and 0 or int(row[2])
            licensing_role_id = License.UNLICENSED
            if not row[3] is None:
                licensing_role_id = int(row[3])
            publisher = ((not row[4] is None) and (row[4] != Publisher.DENY))
            if sysid in cache:
                obj = cache[sysid]
                obj.update_login_at(login_at)
                if admin_level > obj.admin_level:
                    obj.admin_level = admin_level
                if publisher:
                    obj.publisher = True
                obj.update_licensing_role(licensing_role_id)
            else:
                obj = TableauUserEntry(login_at=login_at,
                                       admin_level=admin_level,
                                       licensing_role_id=licensing_role_id,
                                       publisher=publisher)
                cache[sysid] = obj
        return cache

    def _eventit(self, agent, data):
        """Send a read-only password event failed/okay event if
           the user has done setup with a chance to
           configure one and appropriate."""

        # user '0', likely 'palette'
        entry = UserProfile.get(self.server.environment.envid, 0)
            # Potentially send an event only after the user has
            # finished with the "Setup" page (the passowrd will then be
            # there).

        if not entry.hashed_password:
            return

        notification = self.server.notifications.get("dbreadonly")

        if success(data):
            if notification.color == 'red':
                adata = agent.todict()
                self.server.event_control.gen(
                                EventControl.READONLY_DBPASSWORD_OKAY, adata)
                notification.modification_time = func.now()
                notification.color = 'green'
                notification.description = None
                meta.Session.commit()
        else:
            # Failed
            if notification.color != 'red':
                if data['error'].find(
                    "A password is required for this connection.") != -1 or \
                    data['error'].find("password authentication failed") != -1:

                    adata = agent.todict()
                    self.server.event_control.gen(
                                EventControl.READONLY_DBPASSWORD_FAILED, adata)
                    notification.modification_time = func.now()
                    notification.color = 'red'
                    notification.description = None
                    meta.Session.commit()
            return

    @synchronized('auth')
    def load(self, agent, check_odbc_state=True):
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        envid = self.server.environment.envid

        if check_odbc_state and not self.server.odbc_ok():
            return {"error": "Cannot run command while in state: %s" % \
                        self.server.state_manager.get_state()}

        stmt = \
            'SELECT system_users.name, system_users.email, ' +\
            ' system_users.hashed_password, system_users.salt, ' +\
            ' system_users.friendly_name, system_users.admin_level, ' +\
            ' system_users.created_at, system_users.id ' +\
            'FROM system_users'

        excludes = ['guest', '_system']

        data = agent.odbc.execute(stmt)

        # Send tableau readonly password-related events if appropriate.
        self._eventit(agent, data)

        if failed(data):
            return data

        session = meta.Session()

        names = ['palette']
        cache = self.load_users(agent)

        for row in data['']:
            name = row[0]
            if name.lower() in excludes:
                continue

            sysid = row[7]
            names.append(name)

            entry = UserProfile.get_by_name(envid, name)
            if not entry:
                entry = UserProfile(envid=envid, name=name)
                entry.email_level = 0   # disable email by default
                session.add(entry)

            entry.email = row[1]
            entry.hashed_password = row[2]
            entry.salt = row[3]
            entry.friendly_name = row[4]
            entry.system_admin_level = row[5]
            entry.system_created_at = row[6]
            entry.system_user_id = sysid

            if sysid in cache:
                obj = cache[sysid]
                entry.login_at = obj.login_at
                entry.user_admin_level = obj.admin_level
                entry.licensing_role_id = obj.licensing_role_id
                entry.publisher = obj.publisher

        session.commit()

        # deleted entries no longer found in Tableau are marked inactive.
        session.query(UserProfile).\
            filter(not_(UserProfile.name.in_(names))).\
            update({'active': False}, synchronize_session='fetch')

        timestamp = datetime.now().strftime(DATEFMT)
        self.server.system.save(AUTH_TIMESTAMP_SYSTEM_KEY, timestamp)

        d = {u'status': 'OK', u'count': len(data[''])}
        self.server.log.debug("auth load returning: %s", str(d))
        return d

    def verify(self, name, password):
        return UserProfile.verify(self.server.environment.envid, name, password)

class TableauUserEntry(object):

    def __init__(self, login_at=None, admin_level=0,
                 licensing_role_id=License.UNLICENSED, publisher=False):
        self.login_at = login_at
        if not login_at is None:
            if isinstance(login_at, basestring):
                self.login_at = odbc2dt(login_at)
            else:
                self.login_at = login_at
        self.admin_level = admin_level
        self.licensing_role_id = licensing_role_id
        self.publisher = publisher

    def update_login_at(self, login_at):
        if login_at is None:
            return
        if isinstance(login_at, basestring):
            login_at = odbc2dt(login_at)
        if self.login_at is None or login_at > self.login_at:
            self.login_at = login_at

    def update_licensing_role(self, licensing_role_id):
        if licensing_role_id == License.INTERACTOR:
            self.licensing_role_id = License.INTERACTOR
        elif licensing_role_id == License.VIEWER \
                and self.licensing_role_id != License.INTERACTOR:
            self.licensing_role_id = License.VIEWER
