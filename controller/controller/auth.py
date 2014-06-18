import time

from sqlalchemy import not_
from akiri.framework.ext.sqlalchemy import meta

from profile import UserProfile
from system import SystemManager
from util import DATEFMT

class AuthManager(object):

    LAST_IMPORT_KEY = 'last-user-import'

    def __init__(self, server):
        self.server = server

    def load(self, agent):
        stmt = \
            'SELECT system_users.name, system_users.email, ' +\
            ' system_users.hashed_password, system_users.salt, ' +\
            ' system_users.friendly_name, system_users.admin_level, ' +\
            ' system_users.created_at, ' +\
            ' users.login_at, '+\
            ' users.licensing_role_id, users.admin_level, ' +\
            ' users.publisher_tristate ' +\
            'FROM system_users JOIN users ' +\
            'ON system_users.id = users.system_user_id'

        excludes = ['guest', '_system']

        data = agent.odbc.execute(stmt)

        if 'error' in data:
            return data

        session = meta.Session()

        names = ['palette']

        for L in data['']:
            name = L[0]
            if name.lower() in excludes:
                continue

            names.append(name)

            entry = UserProfile.get_by_name(name)
            if not entry:
                entry =  UserProfile(name=name, email=L[1])
            entry.hashed_password = L[2]
            entry.salt = L[3]
            entry.friendly_name=L[4]
            entry.system_admin_level=L[5]
            entry.system_created_at=L[6]
            entry.login_at=L[7]
            entry.licensing_role_id=L[8]
            entry.user_admin_level=L[9]
            entry.publisher_tristate=L[10]
            session.merge(entry)

        # delete entries no longer found in the Tableau database.
        session.query(UserProfile).\
            filter(not_(UserProfile.name.in_(names))).\
            delete(synchronize_session='fetch')

        now = time.strftime(DATEFMT)
        self.server.system.save(self.LAST_IMPORT_KEY, now)

        session.commit()

        ret_dict = {u'status': 'OK',
                u'count': len(data[''])}

        self.server.log.debug("auth load returning: %s", str(ret_dict))

        return ret_dict

    def verify(self, name, password):
        return UserProfile.verify(name, password)
