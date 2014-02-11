import logging
import string
import time
import threading
import platform

import sqlalchemy
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.schema import ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
import meta

from inits import *
class AgentStatusEntry(meta.Base):
    __tablename__ = 'agents'

    uuid = Column(String, primary_key=True)
    hostname = Column(String)
    agent_type = Column(String)
    version = Column(String)
    ip_address = Column(String)
    listen_port = Column(Integer)
    creation_time = Column(DateTime, default=func.now())
    last_connection_time = Column(DateTime, default=func.now())
    last_disconnect_time = Column(DateTime)

    def __init__(self, hostname, agent_type, version, ip_address, listen_port, uuid):
        self.hostname = hostname
        self.agent_type = agent_type
        self.version = version
        self.ip_address = ip_address
        self.listen_port = listen_port
        self.uuid = uuid

    def connected(self):
        if not self.last_disconnect_time:
            return False;
        return self.last_disconnect_time > self.last_connection_time

class AgentStatus(object):

    def __init__(self, log):
        self.log = log
        self.Session = sessionmaker(bind=meta.engine)

    def add(self, hostname, agent_type, version, ip_address, listen_port, uuid):
        session = self.Session()
        entry = AgentStatusEntry(hostname, agent_type, version, ip_address, listen_port, uuid)
        obj =session.merge(entry)
        session.save(obj)
        session.commit()
        session.close()

    def remove(self, hostname):

        session = self.Session()
        #fixme: add try
        session.query(AgentStatusEntry).\
            filter(AgentStatusEntry.hostname == hostname).\
            delete()
        session.commit()
        session.close()
