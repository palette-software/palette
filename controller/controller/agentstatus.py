import logging
import string
import time
import threading
import platform

import sqlalchemy
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, func
from sqlalchemy.schema import ForeignKey, UniqueConstraint
from sqlalchemy.orm.exc import NoResultFound
import meta

class AgentStatusEntry(meta.Base):
    __tablename__ = 'agent'

    # FIXME: Make (domainid, displayname) a unique key.
    agentid = Column(BigInteger, unique=True, nullable=False, \
      autoincrement=True, primary_key=True)
    domainid = Column(BigInteger, ForeignKey("domain.domainid"))
    uuid = Column(String, unique=True, index=True)
    displayname = Column(String)
    hostname = Column(String)
    agent_type = Column(String)
    version = Column(String)
    ip_address = Column(String)
    listen_port = Column(Integer)
    creation_time = Column(DateTime, server_default=func.now())
    modification_time = Column(DateTime, server_default=func.now(), \
      server_onupdate=func.current_timestamp())
    last_connection_time = Column(DateTime, server_default=func.now())
    last_disconnect_time = Column(DateTime)
    UniqueConstraint('domainid', 'displayname')

    def __init__(self, hostname, agent_type, version, ip_address, listen_port, uuid, domainid):
        try:
            # FIXME: shouldn't this be a merge?
            entry = meta.Session.query(AgentStatusEntry).\
                filter(AgentStatusEntry.uuid == uuid).one()
            agentid = entry.agentid
        except NoResultFound, e:
            agentid = None

        self.agentid = agentid
        self.hostname = hostname
        self.agent_type = agent_type
        self.version = version
        self.ip_address = ip_address
        self.listen_port = listen_port
        self.uuid = uuid
        self.domainid = domainid

    def connected(self):
        if not self.last_disconnect_time or \
                        self.last_disconnect_time < self.last_connection_time:
            return True # connected
        else:
            return False # not connected
