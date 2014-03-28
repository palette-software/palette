import socket

from webob import exc

from akiri.framework.api import RESTApplication, DialogPage
from akiri.framework.config import store

import sqlalchemy
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.schema import ForeignKey
from sqlalchemy.orm import sessionmaker

from controller import meta
from controller.agentstatus import AgentStatusEntry
from controller.domain import Domain

class ManageApplication(RESTApplication):

    NAME = 'manage'

    def send_cmd(self, cmd):
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        telnet_port = store.getint("palette", "telnet_port", default=9000)
        telnet_hostname = store.get("palette", "telnet_hostname", default="localhost")
        conn.connect((telnet_hostname, telnet_port))
        conn.send(cmd + '\n')
        print "sent", cmd
        data = conn.recv(3).strip()
        print "got", data
        if data != 'OK':
            # fix me: do something
            print "Bad result back from the controller."
        conn.close()

    def handle_start(self, req):

        self.send_cmd("start")
        return {}

    def handle_stop(self, req):
        self.send_cmd("stop")
        return {}

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
        self.Session = sessionmaker(bind=meta.engine)

        domainname = store.get('palette', 'domainname')
        self.domain = Domain.get_by_name(domainname, Session=self.Session)

        session = self.Session()
        self.agents = session.query(AgentStatusEntry).\
          filter(AgentStatusEntry.domainid == self.domain.domainid).\
          order_by(AgentStatusEntry.last_connection_time.desc()).\
          all()
        for agent in self.agents:
            if agent.connected():
                agent.last_connection_time_str = str(agent.last_connection_time)[:19] # Cut off fraction
                agent.last_disconnect_time_str = "-"
            else:
                agent.last_connection_time_str = str(agent.last_connection_time)[:19] # Cut off fraction
                agent.last_disconnect_time_str = str(agent.last_disconnect_time)[:19] # Cut off fraction
        session.close()
