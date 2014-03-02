import json

import sqlalchemy
from sqlalchemy import Column, String, BigInteger, DateTime, func
from sqlalchemy.orm import sessionmaker

import meta

class XIDEntry(meta.Base):
    __tablename__ = 'xid'

    xid =  Column(BigInteger, unique=True, nullable=False, \
      autoincrement=True, primary_key=True)
    # FIXME: Enumerate valid state values.
    state = Column(String, default='started')
    creation_time = Column(DateTime, server_default=func.now())
    modification_time = Column(DateTime, server_default=func.now(), \
      server_onupdate=func.current_timestamp())

class Request(object):
    """Represents a request.
       Creates a body and adds:
        command: <command>
        xid: <xid>
        body: <body>
    """

    def __init__(self, action, send_body_dict = {}, xid = False):

        self.Session = sessionmaker(bind=meta.engine)

        session = self.Session()

        entry = None
        if xid:
            entry = session.query(XIDEntry).\
                filter(XIDEntry.xid == xid).\
                one()
        else:
            entry = XIDEntry()
            session.add(entry)
            session.commit()
        self.xid = entry.xid

        send_body_dict["action"] = action
        send_body_dict["xid"] = self.xid
        self.send_body = json.dumps(send_body_dict)

        if send_body_dict["action"] == 'cleanup':
            entry.state = "finished"
            session.merge(entry)
            session.commit()

        session.close()

    def __repr__(self):
        return "<action: %s, body_dict: %s, xid: %d>" % \
            (self.action, self.send_body, self.xid)

class Cli_Start_Request(Request):
    def __init__(self, cli_command):
        super(Cli_Start_Request, self).__init__("start", {"cli": cli_command})

class Get_Start_Request(Request):
    def __init__(self, send_body_dict):
        super(Get_Start_Request, self).__init__("start", send_body_dict)

class Cleanup_Request(Request):
    def __init__(self, xid):
        super(Cleanup_Request, self).__init__("cleanup", xid=xid)
