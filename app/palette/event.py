import socket

from webob import exc

from akiri.framework.api import RESTApplication
from akiri.framework.config import store

from controller.meta import Session
from controller.domain import Domain
from controller.event import EventEntry

__all__ = ["EventApplication"]

class EventApplication(RESTApplication):

    NAME = 'events'

    def __init__(self, global_conf):
        super(EventApplication, self).__init__(global_conf)

        domainname = store.get('palette', 'domainname')
        self.domainid = Domain.get_by_name(domainname).domainid

    def handle_get(self, req):
        # Sample requests:
        #   /rest/events?limit=3&start=5&end=7&order=asc
        #
        # start and end can be:
        #   event-id (integer), "now", "epoch", or a datetime.
        #   datetime examples:
        #   2014-04-12
        #   12/04/2013 12:00:00
        #   12/04/2013 12:34:54 PM
        limit = None
        order = None
        start = None
        end = None

        if 'limit' in req.GET:     # max rows to return
            try:
                limit = int(req.GET['limit'])
            except ValueError, e:
                print "Invalid limit:", req.GET['limit']
                raise exc.HTTPBadRequest()

        if 'order' in req.GET:
            order = req.GET['order']
            if order not in ("asc", "desc"):
                print "Invalid order:", order
                raise exc.HTTPBadRequest()

        if 'start' in req.GET:
            start = req.GET['start']
            if start.isdigit():
                start = int(start)
            elif start == 'now':
                start = 'now()'

        if 'end' in req.GET:
            end = req.GET['end']
            if end.isdigit():
                end = int(end)
            elif end == 'now':
                end = u'now()'

        if type(start) == int and end in ('now()', 'epoch'):
            end = None

        if type(end) == int and start in ('now()', 'epoch'):
            start = None

        if start != None and end != None:
            if type(start) != type(end):
                print "Error: Start and end are different types."
                print "type(%s): %s, type(%s): %s" % \
                                        (start, type(start), end, (type(end)))
                raise exc.HTTPBadRequest()

        return self.event_query(start, end, order, limit)

    def event_query(self, start, end, order, limit):
        query = Session.query(EventEntry).\
            filter(EventEntry.domainid == self.domainid)

        if type(start) == int:
            # select based on an event-id
            if order == 'asc':
                if start:
                    query = query.filter(EventEntry.eventid >= start)
                if end:
                    query = query.filter(EventEntry.eventid <= end)
                query = query.order_by(EventEntry.eventid.asc())
            else:
                query = query.filter(EventEntry.eventid <= start)
                if end:
                    query = query.filter(EventEntry.eventid >= end)
                query = query.order_by(EventEntry.eventid.desc())
        else:
            # select based on start, which can be a date,
            # 'epoch' or 'now()'.
            if order == 'asc':
                if start:
                    query = query.filter(EventEntry.creation_time >= start)
                if end:
                    query = query.filter(EventEntry.creation_time <= end)
                query = query.order_by(EventEntry.creation_time.asc())
            else:
                if start:
                    query = query.filter(EventEntry.creation_time <= start)
                if end:
                    query = query.filter(EventEntry.creation_time >= end)
                query = query.order_by(EventEntry.creation_time.desc())

        if limit:
            query = query.limit(limit)

        events = []
        for entry in query:
            events.append({  "eventid": entry.eventid,
                             "title": entry.title,
                             "summary": entry.summary,
                             "description": entry.description,
                             "level": entry.level,
                             "icon": entry.icon,
                             "color": entry.color,
                             "date": str(entry.creation_time)[:19]
                          })
        return events

    def handle(self, req):
        if req.method == "GET":
            return self.handle_get(req)
        else:
            raise exc.HTTPBadRequest()
