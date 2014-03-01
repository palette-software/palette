from sqlalchemy import Column, Integer, BigInteger, String, DateTime, func
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from agentstatus import AgentStatusEntry

import meta
class BackupEntry(meta.Base):
    __tablename__ = 'backup'

    key = Column(Integer, unique=True, nullable=False, primary_key=True)
    agentid = Column(BigInteger, ForeignKey("agents.agentid"))
    name = Column(String)
    creation_time = Column(DateTime, server_default=func.now())
    modification_time = Column(DateTime, server_default=func.now(), \
      server_onupdate=func.current_timestamp())
    UniqueConstraint('agentid', 'name')

    def __init__(self, agentid, name):
        self.agentid = agentid
        self.name = name

class BackupManager(object):

    def __init__(self, domainid):    
        self.Session = sessionmaker(bind=meta.engine)

        self.domainid = domainid

    def add(self, name, agentid):
        session = self.Session()
        entry = BackupEntry(agentid, name)
        session.add(entry)
        session.commit()
        session.close()

    def remove(self, name, agentid):
        session = self.Session()
        # FIXME: Need to figure out how to do this in session.query:
        #        DELETE FROM backup USING agents
        #          WHERE backup.agentid = agents.agentid
        #            AND agents.domainid = self.domainid;
        session.query(BackupEntry).\
            filter(Backup.name == name).\
            filter(Backup.agentid == agentid).delete()
        session.commit()
        session.close()

    def query_by_name(self, name):
        session = self.Session()
        entry = session.query(BackupEntry).\
            join(AgentStatusEntry).\
            filter(AgentStatusEntry.domainid == self.domainid).\
            filter(BackupEntry.name == name).\
            first()
        if entry:
            name = entry.name
        session.close()
        return name
