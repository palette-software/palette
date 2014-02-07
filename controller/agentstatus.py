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
    __tablename__ = 'agentstatus'

    hostname = Column(String, primary_key=True)
    agent_type = Column(String)
    version = Column(String)
    ip_address = Column(String)
    listen_port = Column(Integer)
    uuid = Column(String)
    creation_time = Column(DateTime, default=func.now())

    def __init__(self, hostname, agent_type, version, ip_address, listen_port, uuid):
        self.hostname = hostname
        self.agent_type = agent_type
        self.version = version
        self.ip_address = ip_address
        self.listen_port = listen_port
        self.uuid = uuid

class AgentStatus(object):

    def __init__(self, log):
        self.log = log

        # fixme: move to .ini config file
        if platform.system() == 'Windows':
            # Windows with Tableau uses port 8060
            url = "postgresql://palette:palpass@localhost:8060/paldb"
        else:
            url = "postgresql://palette:palpass@localhost/paldb"

        self.engine = sqlalchemy.create_engine(url, echo=False)

        meta.Base.metadata.create_all(bind=self.engine)
        
        self.Session = sessionmaker(bind=self.engine)

    # Remove all entries to get ready for new agents info.
    def remove_all_agents(self):
        session = self.Session()
        session.query(AgentStatusEntry).\
            delete()

        session.commit()
        session.close()

    def get_all_agents(self):
        agents = self.session.query(AgentStatusEntry).all()
        return agents

    def add(self, hostname, agent_type, version, ip_address, listen_port, uuid):
        session = self.Session()
        entry = AgentStatusEntry(hostname, agent_type, version, ip_address, listen_port, uuid)
        session.add(entry)
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
