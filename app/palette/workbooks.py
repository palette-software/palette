import socket

from webob import exc

from akiri.framework.api import RESTApplication
from akiri.framework.config import store

from controller.meta import Session
from controller.domain import Domain
from controller.workbooks import WorkbookEntry, WorkbookUpdatesEntry

__all__ = ["WorkbookApplication"]

class WorkbookApplication(RESTApplication):

    NAME = 'workbooks'

    def __init__(self, global_conf):
        super(WorkbookApplication, self).__init__(global_conf)

        domainname = store.get('palette', 'domainname')
        self.domainid = Domain.get_by_name(domainname).domainid

    def handle_get(self, req):
        query = Session.query(WorkbookEntry).\
            all()

        workbooks = []
        for entry in query:
            workbook = {}
            workbook['name' ] = entry.name
            workbook['summary'] = entry.summary
            workbook['color'] = entry.color

            update_query = Session.query(WorkbookUpdatesEntry).\
                filter(WorkbookUpdatesEntry.domainid == self.domainid).\
                filter(WorkbookUpdatesEntry.workbookid == entry.workbookid).\
                all()

            updates = []
            for update_entry in update_query:
                update = {}
                update['name'] = update_entry.name
                update['timestamp'] = update_entry.timestamp
                update['url'] = update_entry.url
                updates.append(update)

            workbook['updates'] = updates

            workbooks.append(workbook)

        return {'workbooks': workbooks}

    def handle(self, req):
        if req.method == "GET":
            return self.handle_get(req)
        else:
            raise exc.HTTPBadRequest()
