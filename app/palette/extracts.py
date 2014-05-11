import socket

from webob import exc

from akiri.framework.api import RESTApplication
from akiri.framework.config import store

from controller.meta import Session
from controller.domain import Domain
from controller.extracts import ExtractsEntry

from akiri.framework.api import UserInterfaceRenderer

__all__ = ["ExtractsApplication"]

class Extract(UserInterfaceRenderer):
    TEMPLATE = 'extracts.mako'
    main_active = 'extracts'

def make_extracts(global_conf):
    return Extract(global_conf)

class ExtractsApplication(RESTApplication):

    NAME = 'extracts'

    def __init__(self, global_conf):
        super(ExtractsApplication, self).__init__(global_conf)

        domainname = store.get('palette', 'domainname')
        self.domainid = Domain.get_by_name(domainname).domainid

    def handle_get(self, req):
        query = Session.query(ExtractsEntry).\
            filter(ExtractsEntry.domainid == self.domainid).\
            all()

        extracts = {}
        for entry in query:
            extracts['name' ] = entry.name
            extracts['summary'] = entry.summary
            extracts['description'] = entry.description
            extracts['color'] = entry.color

        return {'extracts': extracts}

    def handle(self, req):
        if req.method == "GET":
            return self.handle_get(req)
        else:
            raise exc.HTTPBadRequest()
