import socket

from webob import exc

from akiri.framework.config import store

from akiri.framework.ext.sqlalchemy import meta

from sqlalchemy import and_, or_

from controller.event import EventEntry
from controller.state_control import StateControl
from controller.event_control import EventControl
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
        html = ""
        for line in entry.description.split('\n'):
            # Replace each leading space with '&nbsp;'
            line_lstripped = line.lstrip(' ')
            lspace_count = len(line) - len(line_lstripped)
            line = '&nbsp;' * lspace_count + line_lstripped

            # Add a break at each line
            html += line + "<br />" + "\n"
        entry.description = html

    def query_mostrecent(self, envid, status=None, event_type=None,
                         timestamp=None, limit=None, publisher=None):
        filters = {}
        filters['envid'] = envid
        q = meta.Session.query(EventEntry).filter(EventEntry.envid == envid)
        if not publisher is None:
            filters['userid'] = publisher
            q = q.filter(EventEntry.userid == publisher)
        if status:
            filters['level'] = status
            q = q.filter(EventEntry.level == status)
        if event_type:
            filters['event_type'] = event_type
            q = q.filter(EventEntry.event_type == event_type)
        if not timestamp is None:
            q = q.filter(EventEntry.timestamp > timestamp)
        q = q.order_by(EventEntry.timestamp.desc())
        if not limit is None:
            q = q.limit(limit)

        events = []
        for event in q.all():
            self.convert_description_to_html(event)
            self.fixup_icon(event)
            events.append(event.todict(pretty=True))

        data = {}
        data['events'] = events
        data['count'] = EventEntry.count(filters)
        return data

    def query_page(self, envid, page, status=None, event_type=None,
                   limit=None, timestamp=None, publisher=None):
        filters = {}
        filters['envid'] = envid
        q = meta.Session.query(EventEntry).filter(EventEntry.envid == envid)
        if not publisher is None:
            filters['userid'] = publisher
            q = q.filter(EventEntry.userid == publisher)
        if status:
            filters['level'] = status
            q = q.filter(EventEntry.level == status)
        if event_type:
            filters['event_type'] = event_type
            q = q.filter(EventEntry.event_type == event_type)
        if not timestamp is None:
            q = q.filter(EventEntry.timestamp <= timestamp)

        if limit is None:
            limit = self.DEFAULT_PAGE_SIZE
        offset = (page - 1) * limit
        q = q.order_by(EventEntry.timestamp.desc()).\
            limit(limit).\
            offset(offset)

        events = []
        for event in q.all():
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
        except:
            pass
        return None

    def getfloat(self, req, name):
        try:
            return float(req.GET[name])
        except:
            pass
        return None

    # ts is epoch seconds as a float.
    def handle_get(self, req):
        timestamp = self.getfloat(req, 'ts')
        if not timestamp is None:
            timestamp = datetime.utcfromtimestamp(timestamp)

        publisher = None
        if req.remote_user.roleid == Role.NO_ADMIN:
            publisher = req.remote_user.system_user_id

        page = self.getint(req, 'page')
        if page is None:
            return self.query_mostrecent(req.envid,
                                         status=self.get(req,'status'),
                                         event_type=self.get(req, 'type'),
                                         timestamp=timestamp,
                                         limit=self.getint(req, 'limit'),
                                         publisher=publisher)
        else:
            return self.query_page(req.envid, page,
                                   status=self.get(req,'status'),
                                   event_type=self.get(req, 'type'),
                                   timestamp=timestamp,
                                   limit=self.getint(req, 'limit'),
                                   publisher=publisher)

    def handle(self, req):
        if req.method == "GET":
            return self.handle_get(req)
        else:
            raise exc.HTTPBadRequest()

