import time

from sqlalchemy import Column, Integer, BigInteger, String, DateTime, func
from sqlalchemy.schema import ForeignKey

from akiri.framework.ext.sqlalchemy import meta

from util import DATEFMT

class EventEntry(meta.Base):
    __tablename__ = "events"

    eventid = Column(BigInteger, unique=True, nullable=False, \
                                   autoincrement=True, primary_key=True)

    envid = Column(BigInteger, ForeignKey("environment.envid"))
    key = Column(String, nullable=False)
    title = Column(String)
    summary = Column(String)
    description = Column(String)
    level = Column(String(1)) # E(rror), W(arning), or I(nfo)
    icon = Column(String)
    color = Column(String)
    event_type = Column(String)
    userid = Column(Integer)
    siteid = Column(Integer)
    projectid = Column(Integer)
    creation_time = Column(DateTime, server_default=func.now())

class EventManager(object):
    def __init__(self, envid):
        self.envid = envid

    def add(self, key, title, description, level, icon, color, event_type,
            userid=None, siteid=None, projectid=None, timestamp=None):
        if timestamp is None:
            summary = time.strftime(DATEFMT)
        else:
            summary = timestamp

        session = meta.Session()
        entry = EventEntry(key=key, envid=self.envid, title=title,
                           description=description, level=level, icon=icon,
                           color=color, event_type=event_type, summary=summary,
                           userid=userid)
        session.add(entry)
        session.commit()
