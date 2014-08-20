from profile import UserProfile
from util import UNDEFINED

# Holds a cache of system_ids per site_id/user_id
class TableauUserCache(object):

    def __init__(self):
        self.data = {}

    def key(self, site_id, user_id):
        return str(site_id) + ':' + str(user_id)

    def add(self, site_id, user_id, system_user_id):
        key = self.key(site_id, user_id)
        self.data[key] = system_user_id

    def get(self, site_id, user_id):
        key = self.key(site_id, user_id)
        if key in self.data:
            return self.data[key]
        return -1


class TableauCacheManager(object):

    # build a cache of the Tableau 'users' table.
    # used to translate siteid:userid -> system_user_id
    def load_users(self, agent):
        stmt = \
            'SELECT system_user_id, site_id, id ' +\
            'FROM users'

        data = agent.odbc.execute(stmt)
        if 'error' in data or not '' in data:
            return {}

        cache = TableauUserCache()
        for row in data['']:
            cache.add(site_id=row[1], user_id=row[2],
                      system_user_id=int(row[0]))
        return cache

    # translate a system_user_id value to the 'username' used by eventgen.
    def get_username_from_system_user_id(self, system_user_id):
        profile = UserProfile.get_by_system_users_id(system_user_id)
        if profile:
            if profile.friendly_name:
                return profile.friendly_name
            else:
                return profile.name
        else:
            return UNDEFINED

    def schema(self, data):
        L = data["$schema"]["Info"]
        return [L[i+1:i+3] for i in xrange(0, len(L), 3)]
