import socket

from webob import exc

from akiri.framework.api import RESTApplication
from akiri.framework.config import store

from akiri.framework.ext.sqlalchemy import meta

from controller.environment import Environment
from controller.event import EventEntry
from controller.state_control import StateControl

__all__ = ["EventApplication"]

class EventApplication(RESTApplication):

    NAME = 'events'

    def __init__(self, global_conf):
        super(EventApplication, self).__init__(global_conf)

        self.envid = Environment.get().envid

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
                if type(start) == int and start > end:
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
        red_count = len(meta.Session.query(EventEntry).\
                    filter(EventEntry.color == StateControl.COLOR_RED).all())
        yellow_count = len(meta.Session.query(EventEntry).\
                    filter(EventEntry.color == StateControl.COLOR_YELLOW).all())
        green_count = len(meta.Session.query(EventEntry).\
                    filter(EventEntry.color == StateControl.COLOR_GREEN).all())

        # Get the list of all event_types found.
        query = meta.Session.query(EventEntry).\
            distinct(EventEntry.event_type).\
            order_by(EventEntry.event_type).\
            all()

        event_types = [entry.event_type for entry in query]

        return { 'event-types': event_types,
                 'red': red_count, 'yellow': yellow_count, 'green': green_count,
                 'events': events }

    def event_query(self, start, end, low, high, order):
#        print "start:", start, ", end:", end, ", low:",low, ", high:", high,
#        print ", order:", order
        query = meta.Session.query(EventEntry).\
            filter(EventEntry.envid == self.envid)

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

            description = ""

            for line in entry.description.split('\n'):
                # Replace each leading space with '&nbsp;'
                line_lstripped = line.lstrip(' ')
                lspace_count = len(line) - len(line_lstripped)
                line = '&nbsp;' * lspace_count + line_lstripped

                # Add a break at each line
                description += line + "<br />" + "\n"

            # FIXME: really use the database table
            if not entry.icon:
                if entry.color == 'green':
                    icon = 'fa-check-circle'
                elif entry.color == 'red':
                    icon = 'fa-times-circle'
                else:
                    icon = 'fa-exclamation-circle'

            events.append({  "eventid": entry.eventid,
                             "title": entry.title,
                             "summary": entry.summary,
                             "description": description,
                             "level": entry.level,
                             "icon": icon,
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
