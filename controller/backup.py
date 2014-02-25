from sqlalchemy import Column, Integer, BigInteger, String, DateTime, func
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

import meta
class BackupEntry(meta.Base):
    __tablename__ = 'backup'

    key = Column(Integer, unique=True, nullable=False, primary_key=True)
    agentid = Column(BigInteger, ForeignKey("agents.agentid"))
    name = Column(String)
    #hostname = Column(String)
    #ip_address = Column(String)
    creation_time = Column(DateTime, default=func.now())
    UniqueConstraint('agentid', 'name')

    def __init__(self, name, agentid):
        self.name = name
        self.agentid = agentid

class BackupManager(object):

    def __init__(self):    
        self.Session = sessionmaker(bind=meta.engine)

    def add(self, name, agentid):
        session = self.Session()
        entry = BackupEntry(name, agentid)
        session.add(entry)
        session.commit()
        session.close()

    def remove(self, name, agentid):
        session = self.Session()
        session.query(BackupEntry).\
            filter(Backup.name == name).\
            filter(Backup.agentid == agentid).delete()
        session.commit()
        session.close()

    def query_by_name(self, name):
        session = self.Session()
        entry = session.query(BackupEntry).\
            filter(BackupEntry.name == name).first()
        if entry:
            name = entry.name
        session.close()
        return name
