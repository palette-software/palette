from sqlalchemy import Column, Integer, BigInteger, String, DateTime, func
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from akiri.framework.ext.sqlalchemy import meta

from agentstatus import AgentStatusEntry

class BackupEntry(meta.Base):
    __tablename__ = 'backup'
    DATEFMT = "%I:%M %p PDT on %B %d, %Y"

    key = Column(Integer, unique=True, nullable=False, primary_key=True)
    volid = Column(BigInteger, ForeignKey("agent_volumes.volid"))
    name = Column(String)
    creation_time = Column(DateTime, server_default=func.now())
    modification_time = Column(DateTime, server_default=func.now(), \
      server_onupdate=func.current_timestamp())
    UniqueConstraint('volid', 'name')

    def todict(self, pretty=False):
        d = {'volid': self.volid,
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

    def add(self, name, volid):
        session = meta.Session()
        entry = BackupEntry(name=name, volid=volid)
        session.add(entry)
        session.commit()

    def remove(self, name, volid):
        session = meta.Session()
        session.query(BackupEntry).\
            filter(BackupEntry.volid == volid).\
            filter(BackupEntry.name == name).\
            delete()
        session.commit()

    @classmethod
    def find_by_name(cls, name):
        entry = meta.Session.query(BackupEntry, AgentStatusEntry).\
            filter(AgentStatusEntry.domainid == self.domainid).\
            filter(BackupEntry.name == name).\
            one()
        return entry

    @classmethod
    def all(cls, domainid, asc=True):
        q = meta.Session.query(BackupEntry)
        if asc:
            q = q.order_by(BackupEntry.creation_time.asc())
        else:
            q = q.order_by(BackupEntry.creation_time.desc())
        return q.all()
