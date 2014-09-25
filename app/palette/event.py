from datetime import datetime
from webob import exc
import cgi

# pylint: disable=import-error,no-name-in-module
from akiri.framework.ext.sqlalchemy import meta
# pylint: enable=import-error,no-name-in-module

from controller.event import EventEntry
from controller.profile import Role

from rest import PaletteRESTHandler

__all__ = ["EventApplication"]

class EventApplication(PaletteRESTHandler):

    NAME = 'events'
    DEFAULT_PAGE_SIZE = 25

    def fixup_icon(self, entry):
        # FIXME: really use the database table
        if not entry.icon:
            if entry.color == 'green':
                icon = 'fa-check-circle'
            elif entry.color == 'red':
                icon = 'fa-times-circle'
            else:
                icon = 'fa-exclamation-circle'
        entry.icon = icon

    def convert_description_to_html(self, entry):
        html = cgi.escape(entry.description)
        html = html.replace('\n', '<br>')
        entry.description = html.replace(' ', '&nbsp;')
        return

    def query_mostrecent(self, envid, status=None, event_type=None,
                         timestamp=None, limit=None, publisher=None):
        # pylint: disable=too-many-arguments
        filters = {}
        filters['envid'] = envid
        query = meta.Session.query(EventEntry).filter(EventEntry.envid == envid)
        if not publisher is None:
            filters['userid'] = publisher
            query = query.filter(EventEntry.userid == publisher)
        if status:
            filters['level'] = status
            query = query.filter(EventEntry.level == status)
        if event_type:
            filters['event_type'] = event_type
            query = query.filter(EventEntry.event_type == event_type)
        if not timestamp is None:
            query = query.filter(EventEntry.timestamp > timestamp)
        query = query.order_by(EventEntry.timestamp.desc())
        if not limit is None:
            query = query.limit(limit)

        events = []
        for event in query.all():
            self.convert_description_to_html(event)
            self.fixup_icon(event)
            events.append(event.todict(pretty=True))

        data = {}
        data['events'] = events
        data['count'] = EventEntry.count(filters)
        return data

    def query_page(self, envid, page, status=None, event_type=None,
                   limit=None, timestamp=None, publisher=None):
        # pylint: disable=too-many-arguments
        filters = {}
        filters['envid'] = envid
        query = meta.Session.query(EventEntry).filter(EventEntry.envid == envid)
        if not publisher is None:
            filters['userid'] = publisher
            query = query.filter(EventEntry.userid == publisher)
        if status:
            filters['level'] = status
            query = query.filter(EventEntry.level == status)
        if event_type:
            filters['event_type'] = event_type
            query = query.filter(EventEntry.event_type == event_type)
        if not timestamp is None:
            query = query.filter(EventEntry.timestamp <= timestamp)

        if limit is None:
            limit = self.DEFAULT_PAGE_SIZE
        offset = (page - 1) * limit
        query = query.order_by(EventEntry.timestamp.desc()).\
                limit(limit).\
                offset(offset)

        events = []
        for event in query.all():
            self.convert_description_to_html(event)
            self.fixup_icon(event)
            events.append(event.todict(pretty=True))

        data = {}
        data['events'] = events
        data['count'] = EventEntry.count(filters)
        return data

    def get(self, req, name):
        if not name in req.GET:
            return None
        value = req.GET[name]
        if value == '0':
            return None
        return value

    def getint(self, req, name):
        try:
            return int(req.GET[name])
        except StandardError:
            pass
        return None

    def getfloat(self, req, name):
        try:
            return float(req.GET[name])
        except StandardError:
            pass
        return None

    # ts is epoch seconds as a float.
    def handle_GET(self, req):
        timestamp = self.getfloat(req, 'ts')
        if not timestamp is None:
            timestamp = datetime.utcfromtimestamp(timestamp)

        publisher = None
        if req.remote_user.roleid == Role.NO_ADMIN:
            publisher = req.remote_user.system_user_id

        page = self.getint(req, 'page')
        if page is None:
            return self.query_mostrecent(req.envid,
                                         status=self.get(req, 'status'),
                                         event_type=self.get(req, 'type'),
                                         timestamp=timestamp,
                                         limit=self.getint(req, 'limit'),
                                         publisher=publisher)
        else:
            return self.query_page(req.envid, page,
                                   status=self.get(req, 'status'),
                                   event_type=self.get(req, 'type'),
                                   timestamp=timestamp,
                                   limit=self.getint(req, 'limit'),
                                   publisher=publisher)

    def handle(self, req):
        if req.method == "GET":
            return self.handle_GET(req)
        else:
            raise exc.HTTPBadRequest()

