import socket
import json

from webob import exc

from akiri.framework.api import RESTApplication
from akiri.framework.config import store

from controller.meta import Session
from controller.domain import Domain
from controller.event import EventEntry

__all__ = ["EventApplication"]

class EventApplication(RESTApplication):

    NAME = 'event'

    def __init__(self, global_conf):
        super(EventApplication, self).__init__(global_conf)

        domainname = store.get('palette', 'domainname')
        self.domainid = Domain.get_by_name(domainname).domainid

    def handle_get(self, req):
        query = Session.query(EventEntry).\
            filter(EventEntry.domainid == self.domainid).\
            order_by(EventEntry.creation_time.desc()).\
            all()

        events = []
        for entry in query:
            events.append({ "eventid": entry.eventid,
                             "text": entry.text,
                             "date": str(entry.creation_time)[:19]
                          })
        return json.dumps(events)

    def handle_post(self, req):
        if 'limit' in req.POST:     # max rows to return
            try:
                limit = int(req.POST['limit'])
            except ValueError, e:
                print "Invalid limit:", limit
                raise exc.HTTPBadRequest()
        else:
            limit = None

        if 'order' in req.POST:
            order = req.POST['order']
            if order not in ("asc", "desc"):
                print "Invalid order:", order
                raise exc.HTTPBadRequest()

        # start and end can be:
        #   event-id (integer), "now", "epoch", or a date-time in the format:
        #   "MM/DD/YY HH:MM:SS"
        if 'start' in req.POST:
            start = req.POST['start']
            if not self.startend_check(start):
                raise exc.HTTPBadRequest()
        else:
            if 'order' == 'asc':
                start = 'now'
            else:
                start = 'epoch'

        if 'end' in req.POST:
            end = req.POST['end']
            if not self.startend_check(end):
                raise exc.HTTPBadRequest()
        else:
            if 'order' == 'desc':
                end = 'epoch'
            else:
                end = 'now'

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
            events.append({ "eventid": entry.eventid,
                             "text": entry.text,
                             "date": str(entry.creation_time)[:19]
                          })
        return json.dumps(events)

    def startend_check(self, incoming):
        """Check the start or end for validity.  Valid is:
                * A number (event-id)
                * 'now' or 'epoch'
                * Date and time: MM/DD/YY HH:MM:SS
            Returns True when valid and False when invalid.
        """
        if type(incoming) == int:
            return True

        if type(incoming) != str:
            return False

        if incoming in ('now', 'epoch'):
            return True

        # To prevent sql injection, accept only this format:
        # MM/DD/YY HH:MM:SS
        valid = "MM/DD/YY HH:MM:SS"
        #        01234567890123456
        #
        if len(incoming) != len(valid):
            print "Wrong date length:", len(incoming), 'for date:', incoming
            return False

        if incoming[2:3] != '/' or incoming[5:6] != '/' or \
                            incoming[11:12] != ':' or incoming[14:15] != ':':
            print "Wrong date format:", incoming
            return False

        # Allow only numbers, '/', ':' and ' '
        pattern = '^[0-9/: ]*$'
        if not re.match(pattern,incoming):
            print "Invalid character(s) in date:", incoming
            return False
        return True


    def handle(self, req):
        if req.method == "GET":
#            return self.test_post(req)     # for testing input
            return self.handle_get(req)
        elif req.method == "POST":
            return self.handle_post(req)    # for specifying what to return
        else:
            raise exc.HTTPBadRequest()

    def test_post(self, req):
        """This can be called in the handle method to test inputs."""
        if 0:
            start = 'now()'
            end = 'epoch'
            order = 'desc'
            limit = 3

        if 0:
            start = 'epoch'
            end = 'now()'
            order = 'asc'
            limit = 3

        if 0:
            start = 1
            end = 5
            order = 'asc'
            limit = 3

        if 0:
            start = 50
            end = 5
            order = 'desc'
            limit = 3

        if 0:
            start = 50
            end = None
            order = 'desc'
            limit = 3

        if 0:
            start = '5/2/2014'
            end = None
            order = 'asc'
            limit = 2

        if 0:
            start = '5/2/2014 09:30:00'
            end = None
            order = 'desc'
            limit = 3

        if 0:
            start = None
            end = '5/2/2014 09:30:00'
            order = 'desc'
            limit = 5

        if 0:
            start = None
            end = '5/2/2014 09:30:00'
            order = 'asc'
            limit = 3

        if 1:
            start = '05/02/2014 09:30:00'
            end = None
            order = 'asc'
            limit = 3

        return self.event_query(start, end, order, limit)
