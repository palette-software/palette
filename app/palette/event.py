import socket

from webob import exc

from akiri.framework.api import RESTApplication
from akiri.framework.config import store

from controller.meta import Session
from controller.domain import Domain
from controller.event import EventEntry
from controller.custom_states import CustomStates

__all__ = ["EventApplication"]

class EventApplication(RESTApplication):

    NAME = 'events'

    def __init__(self, global_conf):
        super(EventApplication, self).__init__(global_conf)

        domainname = store.get('palette', 'domainname')
        self.domainid = Domain.get_by_name(domainname).domainid

    def handle_get(self, req):
        # Event retrieval accepts:
        #   What should be selected from the event table:
        #       start: eventid or a date/time.  Requirement: start <= end
        #       end: eventid or a date/time
        #   You don't have to specify both a start and end.
        #
        #   After the rows are selected by the above 'start' and 'end',
        #   you can choose EITHER "low" or "high".
        #   If "low" is specifified, low/earlier rows are returned.
        #   If "high" is specfieid, high/later rows are returned.
        #   With "low" and "high", you specify the maximum number of rows to return:
        #       low=30 (return the lowest 30 rows)
        #   or
        #       high=30 (return the highest 30 rows)
        # Sample requests:
        #   http://localhost:8080/rest/events?start=3&end=10&low=2&order=asc
        #   http://localhost:8080/rest/events?end=10&high=3&order=asc
        #   http://localhost:8080/rest/events?start=2&end=10&high=3
        #   http://localhost:8080/rest/events?start=2&end=10&low=3
        #   http://localhost:8080/rest/events?start=2&end=10&high=3&order=desc
        # Bad requests:
        #   http://localhost:8080/rest/events?start=now&end=10&low=3
        #       (start=datetime, end=eventid)
        #   http://localhost:8080/rest/events?start=5&end=4&low=3
        #       (end < start)
        # start and end are event-id's or date-related:
        #   event-id (integer), "now", "epoch", or a datetime.
        #   datetime examples:
        #       2014-04-12
        #       12/04/2013 12:00:00
        #       12/04/2013 12:34:54 PM
        start = None
        end = None
        # Can't specify low AND high
        low = None
        high = None

        order = 'asc'   # default

        if 'low' in req.GET:     # max rows to return
            try:
                low = int(req.GET['low'])
            except ValueError, e:
                print "Invalid low:", req.GET['low']
                raise exc.HTTPBadRequest()

        if 'high' in req.GET:     # max rows to return
            try:
                high = int(req.GET['high'])
            except ValueError, e:
                print "Invalid high:", req.GET['high']
                raise exc.HTTPBadRequest()

            if low:
                print "Can't specify both 'low' and 'high'"
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
                # Validity check
                if type(start) == int and end > start:
                        print "Error: start (%d) must be <= end (%d)." % (start, end)
                        raise exc.HTTPBadRequest()
            elif end == 'now':
                end = u'now()'

        # Input validitiy checking
        if start != None and end != None:
            if type(start) != type(end):
                print "Error: Start and end are different types."
                print "type(%s): %s, type(%s): %s" % \
                                        (start, type(start), end, (type(end)))
                raise exc.HTTPBadRequest()

        events = self.event_query(start, end, low, high, order)

        # Count the number of red, yellow and green events.
        red_count = len(Session.query(EventEntry).\
                    filter(EventEntry.color == CustomStates.COLOR_RED).all())
        yellow_count = len(Session.query(EventEntry).\
                    filter(EventEntry.color == CustomStates.COLOR_YELLOW).all())
        green_count = len(Session.query(EventEntry).\
                    filter(EventEntry.color == CustomStates.COLOR_GREEN).all())

        return { 'red': red_count, 'yellow': yellow_count, 'green': green_count,
                                                                'events': events }

    def event_query(self, start, end, low, high, order):
#        print "start:", start, ", end:", end, ", low:",low, ", high:", high,
#        print ", order:", order
        query = Session.query(EventEntry).\
            filter(EventEntry.domainid == self.domainid)

        if type(start) == int or type(end) == int:
            # select based on an event-id
            if start:
                query = query.filter(EventEntry.eventid >= start)
            if end:
                query = query.filter(EventEntry.eventid <= end)

            if low:
                query = query.order_by(EventEntry.eventid.asc())
                query = query.limit(low)
            else:
                query = query.order_by(EventEntry.eventid.desc())
                query = query.limit(high)

            if order == 'asc':
                query = query.from_self().order_by(EventEntry.eventid.asc())
            else:
                query = query.from_self().order_by(EventEntry.eventid.desc())
        else:
            # select based on start, which can be a date,
            # 'epoch' or 'now()'.
            if start:
                query = query.filter(EventEntry.creation_time >= start)
            if end:
                query = query.filter(EventEntry.creation_time <= end)

            if low:
                query = query.order_by(EventEntry.creation_time.asc())
                query = query.limit(low)
            else:
                query = query.order_by(EventEntry.creation_time.desc())
                query = query.limit(high)

            if order == 'asc':
                query = query.from_self().order_by(EventEntry.creation_time.asc())
            else:
                query = query.from_self().order_by(EventEntry.creation_time.desc())

        events = []
        for entry in query:
            events.append({  "eventid": entry.eventid,
                             "title": entry.title,
                             "summary": entry.summary,
                             "description": entry.description,
                             "level": entry.level,
                             "icon": entry.icon,
                             "color": entry.color,
                             "event-type": entry.event_type,
                             "date": str(entry.creation_time)[:19]
                          })
        return events

    def handle(self, req):
        if req.method == "GET":
            return self.handle_get(req)
        else:
            raise exc.HTTPBadRequest()
