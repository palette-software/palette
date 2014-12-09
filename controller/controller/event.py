from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Boolean
from sqlalchemy import Index, func
from sqlalchemy.schema import ForeignKey

# pylint: disable=import-error,no-name-in-module
from akiri.framework.ext.sqlalchemy import meta
# pylint: enable=import-error,no-name-in-module

from mixin import BaseMixin, BaseDictMixin
from util import utctotimestamp

class EventEntry(meta.Base, BaseMixin, BaseDictMixin):
    # pylint: disable=too-many-instance-attributes
    __tablename__ = "events"

    eventid = Column(BigInteger, unique=True, nullable=False, \
                                   autoincrement=True, primary_key=True)

    envid = Column(BigInteger, ForeignKey("environment.envid"))
    # Whether or not the event row is complete/valid.
    complete = Column(Boolean, default=False)

    key = Column(String, nullable=False)
    title = Column(String)
    summary = Column(String)
    description = Column(String)
    level = Column(String(1)) # E(rror), W(arning), or I(nfo)
    icon = Column(String)
    color = Column(String)
    event_type = Column(String)
    userid = Column(Integer)
    site_id = Column(Integer)
    project_id = Column(Integer)
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

Index('events_envid_timestamp_idx', EventEntry.envid, EventEntry.timestamp)
Index('events_envid_level_timestamp_idx', \
          EventEntry.envid, EventEntry.level, EventEntry.timestamp)
Index('events_envid_event_type_timestamp_idx', \
          EventEntry.envid, EventEntry.event_type, EventEntry.timestamp)
