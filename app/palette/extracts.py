import socket

from webob import exc

from akiri.framework.api import RESTApplication
from akiri.framework.config import store

from akiri.framework.ext.sqlalchemy import meta

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
        query = meta.Session.query(ExtractsEntry).\
            filter(ExtractsEntry.domainid == self.domainid).\
            order_by(ExtractsEntry.extractid.asc()).\
            all()

        extracts = []
        for entry in query:
            extract = {'name': entry.name,
                       'summary':entry.summary,
                       'description': entry.description,
                       'color': entry.color}
            extracts.append(extract)

        return {'extracts': extracts}

    def handle(self, req):
        if req.method == "GET":
            return self.handle_get(req)
        else:
            raise exc.HTTPBadRequest()
