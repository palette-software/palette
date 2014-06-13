import time

from sqlalchemy import Column, BigInteger, String, DateTime, func
from sqlalchemy.schema import ForeignKey

from akiri.framework.ext.sqlalchemy import meta

class EventEntry(meta.Base):
    __tablename__ = "events"

    eventid = Column(BigInteger, unique=True, nullable=False, \
                                   autoincrement=True, primary_key=True)

    envid = Column(BigInteger, ForeignKey("environment.envid"))
    title = Column(String)
    summary = Column(String)
    description = Column(String)
    level = Column(String(1)) # E(rror), W(arning), or I(nfo)
    icon = Column(String)
    color = Column(String)
    event_type = Column(String)
    creation_time = Column(DateTime, server_default=func.now())

class EventManager(object):
    DATEFMT = "%I:%M %p PDT on %B %d, %Y"
    
    def __init__(self, envid):
        self.envid = envid

    def add(self, title, description, level, icon, color, event_type):
        summary = time.strftime(self.DATEFMT)

        session = meta.Session()
        entry = EventEntry(envid=self.envid, title=title,
            description=description, level=level, icon=icon, color=color,
                                    event_type=event_type, summary=summary)
        session.add(entry)
        session.commit()
