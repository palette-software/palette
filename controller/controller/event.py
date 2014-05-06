import time
import sqlalchemy
from sqlalchemy import Column, BigInteger, String, DateTime, func
from sqlalchemy.schema import ForeignKey
import meta

class EventEntry(meta.Base):
    __tablename__ = "events"

    eventid = Column(BigInteger, unique=True, nullable=False, \
                                   autoincrement=True, primary_key=True)

    domainid = Column(BigInteger, ForeignKey("domain.domainid"))
    title = Column(String)
    summary = Column(String)
    description = Column(String)
    level = Column(String(1)) # E(rror), W(arning), or I(nfo)
    icon = Column(String)
    color = Column(String)
    creation_time = Column(DateTime, server_default=func.now())

class EventManager(object):
    
    def __init__(self, domainid):
        self.domainid = domainid

    def add(self, title, description, level, icon, color):
        summary = "Event timestamp: " + time.ctime()

        session = meta.Session()
        entry = EventEntry(domainid=self.domainid, title=title,
            description=description, level=level, icon=icon, color=color,
                                                            summary=summary)
        session.add(entry)
        session.commit()
