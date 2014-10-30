from datetime import datetime
from sqlalchemy import Column, String, BigInteger, Integer, DateTime
from sqlalchemy import func, not_, UniqueConstraint
from sqlalchemy.schema import ForeignKey, UniqueConstraint

# pylint: disable=import-error,no-name-in-module
from akiri.framework.ext.sqlalchemy import meta
# pylint: enable=import-error,no-name-in-module

from mixin import BaseMixin, BaseDictMixin
from manager import Manager
from util import DATEFMT

YML_LOCATION_SYSTEM_KEY = 'yml-location'
YML_TIMESTAMP_SYSTEM_KEY = 'yml-timestamp'

class YmlEntry(meta.Base, BaseMixin, BaseDictMixin):
    __tablename__ = "yml"

    ymlid = Column(Integer, unique=True, nullable=False, primary_key=True)
    envid = Column(BigInteger, ForeignKey("environment.envid"),
                   primary_key=True)
    key = Column(String)
    value = Column(String)
    creation_time = Column(DateTime, server_default=func.now())
    modification_time = Column(DateTime, server_default=func.now(),
                               onupdate=func.current_timestamp())

    __table_args__ = (UniqueConstraint('envid', 'key'),)

    @classmethod
    def entry(cls, envid, key, **kwargs):
        filters = {'envid':envid, 'key':key}
        return cls.get_unique_by_keys(filters, **kwargs)

    @classmethod
    def get(cls, envid, key, **kwargs):
        if 'default' in kwargs:
            default = kwargs['default']
            have_default = True
            del kwargs['default']
        else:
            have_default = False

        if kwargs:
            raise ValueError("Invalid kwargs")

        try:
            entry = cls.entry(envid, key, **kwargs)
        except ValueError, ex:
            if have_default:
                return default
            else:
                raise ex
        return entry.value

    @classmethod
    def get_all_by_envid(cls, envid, order_by=None):
        filters = {'envid':envid}
        return cls.get_all_by_keys(filters, order_by=order_by)

    @classmethod
    def last_update(cls, envid):
        filters = {'envid':envid}
        return cls.max('modification_time', filters=filters)

    @classmethod
    def sync(cls, envid, yml):
        """
        Replace all YML entries for a particular environment with passed list.
        The new contents are then returned as a dictionary.
        """
        session = meta.Session()

        d = {}
        # This is the first line ('---')
        for line in yml.strip().split('\n')[1:]:
            key, value = line.split(":", 1)
            value = value.strip()

            entry = cls.entry(envid, key, default=None)
            if entry is None:
                entry = cls(envid=envid, key=key)
            entry.value = value
            session.add(entry)
            d[key] = value

        session.query(cls).\
            filter(not_(cls.key.in_(d.keys()))).\
            delete(synchronize_session='fetch')

        session.commit()
        return d


class YmlManager(Manager):

    def get(self, key, **kwargs):
        return YmlEntry.get(self.envid, key, **kwargs)

    # This method can throw IOError
    def sync(self, agent):
        path = agent.path.join(agent.tableau_data_dir, "data", "tabsvc",
                               "config", "workgroup.yml")
        if not agent.displayname:
            location = agent.hostname + ' - ' + path
        else:
            location = agent.displayname + ' - ' + path
        timestamp = datetime.now().strftime(DATEFMT)
        contents = agent.filemanager.get(path)
        body = YmlEntry.sync(self.envid, contents)
        self.server.system.save(YML_LOCATION_SYSTEM_KEY, location)
        self.server.system.save(YML_TIMESTAMP_SYSTEM_KEY, timestamp)
        return body
