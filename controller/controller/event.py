from sqlalchemy import Column, Integer, BigInteger, String, DateTime, func
# from sqlalchemy import Index
from sqlalchemy.schema import ForeignKey

# pylint: disable=import-error,no-name-in-module
from akiri.framework.ext.sqlalchemy import meta
# pylint: enable=import-error,no-name-in-module

from mixin import BaseMixin, BaseDictMixin
from util import utctotimestamp

class EventEntry(meta.Base, BaseMixin, BaseDictMixin):
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
    timestamp = Column(DateTime, server_default=func.now())

    def todict(self, pretty=False, exclude=None):
        if exclude is None:
            exclude = []
        data = super(EventEntry, self).todict(pretty=pretty, exclude=exclude)

        timestamp = "%.6f" % utctotimestamp(self.timestamp)
        if pretty:
            data['reference-time'] = timestamp
        else:
            data['reference_time'] = timestamp
        return data

# Index('idx', EventEntry.envid, EventEntry.timestamp.desc())
