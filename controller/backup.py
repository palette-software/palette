from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.schema import ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

import meta
class BackupEntry(meta.Base):
    __tablename__ = 'backup'

    name = Column(String, primary_key=True)
    ip_address = Column(String)
    creation_time = Column(DateTime, default=func.now())

    def __init__(self, name, ip_address):
        self.name = name
        self.ip_address = ip_address

class BackupManager(object):

    def __init__(self, engine):
    
        self.Session = sessionmaker(bind=engine)

    def add(self, name, ip_address):
        session = self.Session()
        entry = BackupEntry(name, ip_address)
        session.add(entry)
        session.commit()
        session.close()

    def remove(self, name, ip_address):
        session = self.Session()
        session.query(BackupEntry).\
            filter(Backup.entry == name).\
            filter(Backup.ip_address == ip_address).delete()
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
