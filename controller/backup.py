from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

import meta
class BackupEntry(meta.Base):
    __tablename__ = 'backup'

    key = Column(Integer, primary_key=True)
    uuid = Column(String, ForeignKey("agents.uuid"))
    name = Column(String)
    #hostname = Column(String)
    #ip_address = Column(String)
    creation_time = Column(DateTime, default=func.now())
    UniqueConstraint('uuid', 'name')

    def __init__(self, name, uuid):
        self.name = name
        self.uuid = uuid

class BackupManager(object):

    def __init__(self):    
        self.Session = sessionmaker(bind=meta.engine)

    def add(self, name, uuid):
        session = self.Session()
        entry = BackupEntry(name, uuid)
        session.add(entry)
        session.commit()
        session.close()

    def remove(self, name, uuid):
        session = self.Session()
        session.query(BackupEntry).\
            filter(Backup.name == name).\
            filter(Backup.uuid == uuid).delete()
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
