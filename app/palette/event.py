from collections import OrderedDict
from datetime import datetime
from webob import exc
import re

import akiri.framework.sqlalchemy as meta

from controller.event import EventEntry
from controller.profile import Role

__all__ = ["EventHandler"]

class EventHandler(object):

    NAME = 'events'
    DEFAULT_PAGE_SIZE = 25

    def fixup_icon(self, data):
        if 'icon' in data:
            icon = data['icon']
        else:
            icon = None
        # FIXME: really use the database table
        if not icon:
            color = data['color']
            if color == 'green':
                icon = 'fa-check-circle'
            elif color == 'red':
                icon = 'fa-times-circle'
            else:
                icon = 'fa-exclamation-circle'
        data['icon'] = icon

    def convert_description_to_html(self, data):
        html = data['description'].replace('\n', '<br>')
        # Replace leading spaces with '&nbsp;'
        html = re.sub(r'^ +', lambda m: '&nbsp;'*len(m.group()), html)
        data['description'] = html
        return

    def query_mostrecent(self, envid, status=None, event_type=None,
                         timestamp=None, limit=None, publisher=None):
        # pylint: disable=too-many-arguments
        # pylint: disable=maybe-no-member
        filters = OrderedDict({'envid': envid})

        if not publisher is None:
            filters['userid'] = publisher
        if status:
            filters['level'] = status
        if event_type:
            filters['event_type'] = event_type

        query = meta.Session.query(EventEntry)
        query = EventEntry.apply_filters(query, filters)

        # timestamp filter is deliberately not included in the count().
        if not timestamp is None:
            query = query.filter(EventEntry.timestamp > timestamp)

        query = query.order_by(EventEntry.timestamp.desc())
        if not limit is None:
            query = query.limit(limit)

        events = []
        for event in query.all():
            if not event.complete:
                continue
            evdict = event.todict(pretty=True)
            self.convert_description_to_html(evdict)
            self.fixup_icon(evdict)
            events.append(evdict)

        data = {}
        data['events'] = events
        data['count'] = EventEntry.count(filters) # FIXME: approximate?
        return data

    def query_page(self, envid, page, status=None, event_type=None,
                   limit=None, timestamp=None, publisher=None):
        # pylint: disable=too-many-arguments
        # pylint: disable=maybe-no-member
        filters = OrderedDict({'envid': envid})

        if not publisher is None:
            filters['userid'] = publisher
        if status:
            filters['level'] = status
        if event_type:
            filters['event_type'] = event_type

        query = meta.Session.query(EventEntry)
        query = EventEntry.apply_filters(query, filters)

        # timestamp filter is deliberately not included in the count().
        if not timestamp is None:
            query = query.filter(EventEntry.timestamp > timestamp)

        if limit is None:
            limit = self.DEFAULT_PAGE_SIZE
        offset = (page - 1) * limit
        query = query.order_by(EventEntry.timestamp.desc()).\
                limit(limit).\
                offset(offset)

        events = []
        for event in query.all():
            evdict = event.todict(pretty=True)
            self.convert_description_to_html(evdict)
            self.fixup_icon(evdict)
            events.append(evdict)

        data = {}
        data['events'] = events
        data['count'] = EventEntry.count(filters)
        return data

    # ts is epoch seconds as a float.
    def handle_GET(self, req):
        timestamp = req.params_getfloat('ts')
        if not timestamp is None:
            timestamp = datetime.utcfromtimestamp(timestamp)

        publisher = None
        if req.remote_user.roleid == Role.NO_ADMIN:
            publisher = req.remote_user.userid

        page = req.params_getint('page')
        if page is None:
            return self.query_mostrecent(req.envid,
                                         status=req.params_get('status'),
                                         event_type=req.params_get('type'),
                                         timestamp=timestamp,
                                         limit=req.params_getint('limit'),
                                         publisher=publisher)
        else:
            return self.query_page(req.envid, page,
                                   status=req.params_get('status'),
                                   event_type=req.params_get('type'),
                                   timestamp=timestamp,
                                   limit=req.params_getint('limit'),
                                   publisher=publisher)

    def handle(self, req):
        if req.method == "GET":
            return self.handle_GET(req)
        else:
            raise exc.HTTPBadRequest()

