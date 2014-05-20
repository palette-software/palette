import meta

from profile import UserProfile

class AuthManager(object):

    def __init__(self, server):
        self.server = server

    def load(self, aconn):
        stmt = \
            'SELECT name,email,hashed_password,salt,friendly_name ' +\
            'FROM system_users'
        data = aconn.odbc.execute(stmt)

        if 'error' in data:
            return data

        session = meta.Session()
        # FIXME: do this is a better way.
        session.query(UserProfile).\
            filter(UserProfile.name != 'palette').delete()

        for L in data['']:
            entry = UserProfile(name=L[0], email=L[1], hashed_password=L[2],
                                salt=L[3], friendly_name=L[4])
            session.add(entry)
        session.commit()

        return {u'status': 'OK',
                u'count': len(data[''])}

    def verify(self, name, password):
        return UserProfile.verify(name, password)
