import sqlalchemy
from sqlalchemy import Column, BigInteger, String, DateTime, func
from sqlalchemy.schema import ForeignKey
import meta

class EventEntry(meta.Base):
    __tablename__ = "events"

    eventid = Column(BigInteger, unique=True, nullable=False, \
                                   autoincrement=True, primary_key=True)

    domainid = Column(BigInteger, ForeignKey("domain.domainid"))
    text = Column(String)
    creation_time = Column(DateTime, server_default=func.now())

class EventManager(object):
    
    def __init__(self, domainid):
        self.domainid = domainid

    def add(self, text):
        session = meta.Session()
        entry = EventEntry(domainid=self.domainid, text=text)
        session.add(entry)
        session.commit()
