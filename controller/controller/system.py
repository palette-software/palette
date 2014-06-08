from sqlalchemy import Column, String, BigInteger, DateTime, func, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.schema import ForeignKey, UniqueConstraint

from akiri.framework.ext.sqlalchemy import meta
from mixin import BaseMixin, BaseDictMixin

class SystemEntry(meta.Base, BaseMixin, BaseDictMixin):
    __tablename__ = 'system'

    domainid = Column(BigInteger, ForeignKey("domain.domainid"), primary_key=True)
    key = Column(String, unique=True, nullable=False, primary_key=True)
    value = Column(String)
    creation_time = Column(DateTime, server_default=func.now())
    modification_time = Column(DateTime, server_default=func.now(),
                               onupdate=func.current_timestamp())

    defaults = [{'name':'disk-watermark-low', 'value':str(50)},
                {'name':'disk-watermark-low', 'value':str(80)}]
                
class SystemManager(object):

    # Keys
    SYSTEM_KEY_STATE = "state"
    SYSTEM_KEY_EVENT_SUMMARY_FORMAT = "event-summary-format"
    SYSTEM_KEY_ARCHIVE_BACKUP_LOCATION = "archive-backup-location"

    def __init__(self, domainid):
        self.domainid = domainid

    def save(self, key, value):
        session = meta.Session()

        entry = SystemEntry(domainid=self.domainid, key=key, value=value)
        session.merge(entry)
        session.commit()

    def entry(self, key):
        try:
            entry = meta.Session.query(SystemEntry).\
                filter(SystemEntry.domainid == self.domainid).\
                filter(SystemEntry.key == key).\
                one()
        except NoResultFound, e:
            raise ValueError("No system row found with key=%s" % key)
        return entry

    def get(self, key):
        entry = self.entry(key)
        return entry.value

    @classmethod
    def populate(cls):
        SystemEntry.populate()
