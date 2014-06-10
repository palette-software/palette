import socket

from webob import exc

from akiri.framework.api import RESTApplication, DialogPage
from akiri.framework.config import store

import sqlalchemy
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.schema import ForeignKey

from akiri.framework.ext.sqlalchemy import meta

from controller.agent import Agent
from controller.domain import Domain

from page import PalettePage
from rest import PaletteRESTHandler, required_parameters

class ManageApplication(PaletteRESTHandler):

    NAME = 'manage'

    def handle_start(self, req):
        self.telnet.send_cmd("start")
        return {}

    def handle_stop(self, req):
        self.telnet.send_cmd("stop")
        return {}

    @required_parameters('action')
    def handle(self, req):
        if req.method != "POST":
            raise exc.HTTPMethodNotAllowed()
        action = req.POST['action'].lower()
        if action == 'start':
            return self.handle_start(req)
        elif action == 'stop':
            return self.handle_stop(req)
        raise exc.HTTPBadRequest()

class ManageAdvancedDialog(DialogPage):

    NAME = "manage"
    TEMPLATE = "manage.mako"

    def __init__(self, global_conf):
        super(ManageAdvancedDialog, self).__init__(global_conf)

        domainname = store.get('palette', 'domainname')
        self.domain = Domain.get_by_name(domainname)

        self.agents = meta.Session.query(Agent).\
          filter(Agent.domainid == self.domain.domainid).\
          order_by(Agent.last_connection_time.desc()).\
          all()
        for agent in self.agents:
            if agent.connected():
                agent.last_connection_time_str = str(agent.last_connection_time)[:19] # Cut off fraction
                agent.last_disconnect_time_str = "-"
            else:
                agent.last_connection_time_str = str(agent.last_connection_time)[:19] # Cut off fraction
                agent.last_disconnect_time_str = str(agent.last_disconnect_time)[:19] # Cut off fraction

class Manage(PalettePage):
    TEMPLATE = 'manage.mako'
    active = 'manage'

def make_manage(global_conf):
    return Manage(global_conf)
