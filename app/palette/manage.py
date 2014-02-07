import socket

from webob import exc

from akiri.framework.api import RESTApplication, DialogPage

import sqlalchemy
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.schema import ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
import meta
from . import Session

PORT=9000    # fixme: get from somewhere else

class ManageApplication(RESTApplication):

    NAME = 'manage'

    def send_cmd(self, cmd):
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect(("", PORT))
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

class AgentStatusEntry(meta.Base):
    __tablename__ = 'agentstatus'

    hostname = Column(String, primary_key=True)
    agent_type = Column(String)
    version = Column(String)
    ip_address = Column(String)
    listen_port = Column(Integer)
    uuid = Column(String)
    creation_time = Column(DateTime, default=func.now())
        
class ManageAdvancedDialog(DialogPage):

    NAME = "manage"
    TEMPLATE = "manage.mako"

    def __init__(self, global_conf):
        super(ManageAdvancedDialog, self).__init__(global_conf)

        db_session = Session()
        self.agents = db_session.query(AgentStatusEntry).all()
        db_session.close()
