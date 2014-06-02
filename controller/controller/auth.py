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
        session.query(UserProfile).\
            filter(UserProfile.name != 'palette').delete()

        for L in data['']:
            entry = UserProfile(name=L[0], email=L[1], hashed_password=L[2],
                                salt=L[3], friendly_name=L[4],
                                licensing_role_id=L[5], admin_level=L[6],
                                publisher_tristate=L[7],
                                created_at=L[8], updated_at=L[9])
            session.add(entry)
        session.commit()

        return {u'status': 'OK',
                u'count': len(data[''])}

    def verify(self, name, password):
        return UserProfile.verify(name, password)
