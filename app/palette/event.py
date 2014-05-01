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

    def handle(self, req):
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
