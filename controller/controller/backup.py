from sqlalchemy import Column, Integer, BigInteger, String, DateTime, func
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from agentstatus import AgentStatusEntry
import meta

class BackupEntry(meta.Base):
    __tablename__ = 'backup'
    DATEFMT = "%I:%M %p on %A, %B %d, %Y"

    key = Column(Integer, unique=True, nullable=False, primary_key=True)
    agentid = Column(BigInteger, ForeignKey("agent.agentid"))
    name = Column(String)
    creation_time = Column(DateTime, server_default=func.now())
    modification_time = Column(DateTime, server_default=func.now(), \
      server_onupdate=func.current_timestamp())
    UniqueConstraint('agentid', 'name')
    agent = relationship("AgentStatusEntry")

    def __init__(self, agentid, name):
        self.agentid = agentid
        self.name = name

    def todict(self, pretty=False):
        d = {'agent': self.agent.displayname,
             'name': self.name}
        if pretty:
            d['creation-time'] = self.creation_time.strftime(self.DATEFMT)
            d['modification-time'] = self.modification_time.strftime(self.DATEFMT)
        else:
            d['creation_time'] = str(self.creation_time)
            d['modification_time'] = str(self.modification_time)
        return d


class BackupManager(object):

    def __init__(self, domainid):
        self.domainid = domainid

    def add(self, name, agentid):
        session = meta.Session()
        entry = BackupEntry(agentid, name)
        session.add(entry)
        session.commit()

    def remove(self, name, agentid):
        session = meta.Session()
        session.query(BackupEntry).\
            filter(Backup.name == name).\
            filter(Backup.agentid == agentid).delete()
        session.commit()

    @classmethod
    def all(cls, domainid, asc=True):
        q = meta.Session.query(BackupEntry).\
            join(AgentStatusEntry).\
            filter(AgentStatusEntry.domainid == domainid)
        if asc:
            q = q.order_by(BackupEntry.creation_time.asc())
        else:
            q = q.order_by(BackupEntry.creation_time.desc())
        return q.all()
