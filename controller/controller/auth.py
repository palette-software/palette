from sqlalchemy import not_
from akiri.framework.ext.sqlalchemy import meta

from profile import UserProfile

class AuthManager(object):

    def __init__(self, server):
        self.server = server

    def load(self, aconn):
        stmt = \
            'SELECT system_users.name, system_users.email, ' +\
            ' system_users.hashed_password, system_users.salt, ' +\
            ' system_users.friendly_name, ' +\
            ' users.licensing_role_id, users.admin_level, ' +\
            ' users.publisher_tristate, users.created_at, users.updated_at ' +\
            'FROM system_users JOIN users ' +\
            'ON system_users.id = users.system_user_id'

        data = aconn.odbc.execute(stmt)

        if 'error' in data:
            return data

        session = meta.Session()
        # FIXME: do this is a better way.
        #session.query(UserProfile).\
        #    filter(UserProfile.name != 'palette').delete()

        names = ['palette']

        for L in data['']:
            name = L[0]
            names.append(name)

            entry = UserProfile.get_by_name(name)
            if not entry:
                entry =  UserProfile(name=name, email=L[1])
            entry.hashed_password = L[2]
            entry.salt = L[3]
            entry.friendly_name=L[4],
            entry.licensing_role_id=L[5]
            entry.admin_level=L[6]
            entry.publisher_tristate=L[7]
            entry.created_at=L[8]
            entry.updated_at=L[9]
            session.merge(entry)

        # delete entries no longer found in the Tableau database.
        session.query(UserProfile).\
            filter(not_(UserProfile.name.in_(names))).\
            delete(synchronize_session='fetch')

        session.commit()

        return {u'status': 'OK',
                u'count': len(data[''])}

    def verify(self, name, password):
        return UserProfile.verify(name, password)
