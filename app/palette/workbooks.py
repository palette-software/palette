import socket

from webob import exc

from akiri.framework.api import RESTApplication
from akiri.framework.config import store

from akiri.framework.ext.sqlalchemy import meta

from controller.domain import Domain
from controller.workbooks import WorkbookEntry
from controller.util import UNDEFINED
from controller.profile import UserProfile

from rest import PaletteRESTHandler

__all__ = ["WorkbookApplication"]

class WorkbookApplication(PaletteRESTHandler):

    NAME = 'workbooks'

    def getuser_fromdb(self, system_users_id):
        if system_users_id < 0:
            return UNDEFINED
        user = UserProfile.get_by_system_users_id(system_users_id)
        if not user:
            return UNDEFINED
        return user.display_name()

    def getuser(self, system_users_id, cache={}):
        if system_users_id in cache:
            return cache[system_users_id]
        user = self.getuser_fromdb(system_users_id)
        cache[system_users_id] = user
        return user

    def handle_get(self, req):

        users = {}

        workbooks = []
        for entry in WorkbookEntry.get_all_by_envid(self.envid):
            data = entry.todict(pretty=True)

            updates = []
            for update in entry.updates:
                d = update.todict(pretty=True)
                d['username'] = self.getuser(update.system_users_id, users)
                updates.append(d)
            data['updates'] = updates

            if entry.updates:
                # The summary field contains the name of the current owner,
                # which can be found from the last (by-time) update entry.
                system_users_id = entry.updates[0].system_users_id
                data['summary'] = self.getuser(system_users_id, users)

            workbooks.append(data)

        return {'workbooks': workbooks}

    def handle(self, req):
        if req.method == "GET":
            return self.handle_get(req)
        else:
            raise exc.HTTPBadRequest()
