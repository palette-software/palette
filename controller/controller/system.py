import re

from sqlalchemy import Column, String, Integer, BigInteger, DateTime, Boolean
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.schema import ForeignKey, UniqueConstraint

from akiri.framework.ext.sqlalchemy import meta
from mixin import BaseMixin, BaseDictMixin

from manager import Manager
from general import SystemConfig
from files import FileManager

class SystemEntry(meta.Base, BaseMixin, BaseDictMixin):
    __tablename__ = 'system'

    # FIXME: integer
    envid = Column(BigInteger, ForeignKey("environment.envid"),
                   primary_key=True)
    key = Column(String, unique=True, nullable=False, primary_key=True)
    value = Column(String)
    creation_time = Column(DateTime, server_default=func.now())
    modification_time = Column(DateTime, server_default=func.now(),
                               onupdate=func.current_timestamp())

    defaults = [{'envid':1, 'key':'disk-watermark-low', 'value':str(50)},
                {'envid':1, 'key':'disk-watermark-high', 'value':str(80)},
                {'envid':1, 'key':SystemConfig.STORAGE_ENCRYPT, 'value': 'no'},
                {'envid':1,
                 'key':SystemConfig.WORKBOOKS_AS_TWB,
                 'value': 'no'},
                {'envid':1,
                 'key':SystemConfig.BACKUP_AUTO_RETAIN_COUNT,
                 'value': '3'},
                {'envid':1,
                 'key':SystemConfig.BACKUP_USER_RETAIN_COUNT,
                 'value': '5'},
                {'envid':1,
                 'key':SystemConfig.BACKUP_DEST_TYPE,
                 'value': FileManager.STORAGE_TYPE_VOL},
                {'envid':1,
                 'key':SystemConfig.LOG_ARCHIVE_RETAIN_COUNT,
                 'value': '5'},
                {'envid':1, 'key':'http-load-warn', 'value':str(10)},
                {'envid':1, 'key':'http-load-error', 'value':str(20)}
        # Note: No default volid set.
    ]

    @classmethod
    def get_by_key(cls, envid, key, **kwargs):
        filters = {'envid':envid, 'key':key}
        return cls.get_unique_by_keys(filters, **kwargs)

    @classmethod
    def get_all(cls, envid):
        filters = {'envid':envid}
        return cls.get_all_by_keys(filters)


# Merge with 'System' in the webapp.
class SystemManager(Manager):

    # Keys
    SYSTEM_KEY_STATE = "state"
    SYSTEM_KEY_EVENT_SUMMARY_FORMAT = "event-summary-format"

    def save(self, key, value):
        session = meta.Session()

        entry = SystemEntry(envid=self.envid, key=key, value=value)
        session.merge(entry)
        session.commit()

    def entry(self, key, **kwargs):
        return SystemEntry.get_by_key(self.envid, key, **kwargs)

    def get(self, key, **kwargs):
        if 'default' in kwargs:
            default = kwargs['default']
            have_default = True
            del kwargs['default']
        else:
            have_default = False

        if kwargs:
            raise ValueError("Invalid kwargs")

        try:
            entry = self.entry(key)
        except ValueError, e:
            if have_default:
                return default
            else:
                raise e
        return entry.value

    def getint(self, key, **kwargs):
        return int(self.get(key, **kwargs))

    # entire system table to a dictionary
    def todict(self, pretty=False):
        d = {}
        for entry in SystemEntry.get_all(self.envid):
            key = entry.key
            if not pretty:
                key = key.replace('-','_')
            else:
                key = key.replace('_','-')
            d[key] = entry.value
        return d

    @classmethod
    def populate(cls):
        SystemEntry.populate()

class LicenseEntry(meta.Base, BaseMixin, BaseDictMixin):
    __tablename__ = 'license'

    licenseid = Column(BigInteger, primary_key=True)
    agentid = Column(BigInteger, ForeignKey("agent.agentid"),
                     nullable=False, unique=True)
    interactors = Column(Integer)
    viewers = Column(Integer)
    notified = Column(Boolean, nullable=False, default=False)
    creation_time = Column(DateTime, server_default=func.now())
    modification_time = Column(DateTime, server_default=func.now(),
                               onupdate=func.current_timestamp())

    @classmethod
    def get_by_agentid(cls, agentid):
        try:
            entry = meta.Session.query(LicenseEntry).\
                filter(LicenseEntry.agentid == agentid).\
                one()
        except NoResultFound, e:
            return None
        return entry

    @classmethod
    def get(cls, agentid, interactors=None, viewers=None):
        session = meta.Session()
        entry = cls.get_by_agentid(agentid)
        if not entry:
            entry = LicenseEntry(agentid=agentid)
            session.add(entry)

        entry.interactors = interactors
        entry.viewers = viewers

        # If the entry is valid, reset the notification field.
        if entry.valid():
            entry.notified = False

        return entry

    @classmethod
    def parse(cls, output):
        pattern = '(?P<interactors>\d+) interactors, (?P<viewers>\d+) viewers'
        m = re.search(pattern, output)
        if not m:
            return {}
        return m.groupdict()

    def invalid(self):
        if self.interactors is None:
            return False
        self.interactors = int(self.interactors)
        if self.viewers is None:
            return False
        self.viewers = int(self.viewers)
        return self.interactors == 0 and self.viewers == 0

    def valid(self):
        return not self.invalid()

    def gettype(self):
        if self.interactors is None and self.viewers is None:
            return "Core"
        else:
            return "Named-user"

    def capacity(self):
        if self.interactors is None and self.viewers is None:
            return None
        return "%d interactors, %d viewers" % (self.interactors, self.viewers)
