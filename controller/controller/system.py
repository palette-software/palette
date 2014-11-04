from sqlalchemy import Column, String, BigInteger, DateTime
from sqlalchemy import func
from sqlalchemy.schema import ForeignKey

# pylint: disable=import-error,no-name-in-module
from akiri.framework.ext.sqlalchemy import meta
# pylint: enable=import-error,no-name-in-module

from mixin import BaseMixin, BaseDictMixin
from manager import Manager
from general import SystemConfig
from files import FileManager

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
                {'envid':1, 'key':'http-load-error', 'value':str(20)},
                {'envid':1, 'key':'http-load-re', 'value':r'.+\.xml(\Z\?)'},
                {'envid':1, 'key':'ping-request-interval', 'value':str(10)},
                {'envid':1, 'key':'socket-timeout', 'value':str(60)},
                {'envid':1, 'key':'ssl-handshake-timeout', 'value':str(5)},
                {'envid':1, 'key':'event-degraded-min', 'value':str(180)},
                {'envid':1, 'key':'status-request-interval', 'value':str(10)},
                {'envid':1, 'key': SystemConfig.ALERTS_ENABLED, 'value':'no'},
                {'envid':1, 'key': SystemConfig.UPGRADING, 'value':'no'}
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
        except ValueError, ex:
            if have_default:
                return default
            else:
                raise ex
        return entry.value

    def delete(self, key, synchronize_session='evaluate'):
        filters = {'envid':self.envid, 'key':key}
        SystemEntry.delete(filters, synchronize_session=synchronize_session)

    def getint(self, key, **kwargs):
        return int(self.get(key, **kwargs))

    # entire system table to a dictionary
    def todict(self, pretty=False):
        d = {}
        for entry in SystemEntry.get_all(self.envid):
            key = entry.key
            if not pretty:
                key = key.replace('-', '_')
            else:
                key = key.replace('_', '-')
            d[key] = entry.value
        return d

    @classmethod
    def populate(cls):
        SystemEntry.populate()
