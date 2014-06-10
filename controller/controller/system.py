from sqlalchemy import Column, String, Integer, BigInteger, DateTime, func
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.schema import ForeignKey, UniqueConstraint

from akiri.framework.ext.sqlalchemy import meta
from mixin import BaseMixin, BaseDictMixin

class SystemEntry(meta.Base, BaseMixin, BaseDictMixin):
    __tablename__ = 'system'

    envid = Column(BigInteger, ForeignKey("environment.envid"),
                   primary_key=True)
    key = Column(String, unique=True, nullable=False, primary_key=True)
    value = Column(String)
    creation_time = Column(DateTime, server_default=func.now())
    modification_time = Column(DateTime, server_default=func.now(),
                               onupdate=func.current_timestamp())

    defaults = [{'envid':1, 'key':'disk-watermark-low', 'value':str(50)},
                {'envid':1, 'key':'disk-watermark-high', 'value':str(80)}]
                
class SystemManager(object):

    # Keys
    SYSTEM_KEY_STATE = "state"
    SYSTEM_KEY_EVENT_SUMMARY_FORMAT = "event-summary-format"
    SYSTEM_KEY_ARCHIVE_BACKUP_LOCATION = "archive-backup-location"

    def __init__(self, envid):
        self.envid = envid

    def save(self, key, value):
        session = meta.Session()

        entry = SystemEntry(envid=self.envid, key=key, value=value)
        session.merge(entry)
        session.commit()

    def entry(self, key):
        try:
            entry = meta.Session.query(SystemEntry).\
                filter(SystemEntry.envid == self.envid).\
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

class LicenseEntry(meta.Base, BaseMixin, BaseDictMixin):
    __tablename__ = 'license'

    licenseid = Column(BigInteger, primary_key=True)
    agentid = Column(BigInteger, ForeignKey("agent.agentid"))
    interactors = Column(Integer, nullable=False)
    viewers = Column(Integer, nullable=False)
    creation_time = Column(DateTime, server_default=func.now())
    modification_time = Column(DateTime, server_default=func.now(),
                               onupdate=func.current_timestamp())

    @classmethod
    def save(cls, agentid, interactors, viewers):
        session = meta.Session()
        entry = SystemEntry(agentid=agentid,
                            interactor=interactors,
                            viewers=viewers)
        session.merge(entry)
        session.commit()
