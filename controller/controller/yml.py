import yaml

from datetime import date
from datetime import datetime
from sqlalchemy import Column, String, BigInteger, Integer, DateTime
from sqlalchemy import func, not_, UniqueConstraint
from sqlalchemy.schema import ForeignKey, UniqueConstraint

import akiri.framework.sqlalchemy as meta

from mixin import BaseMixin, BaseDictMixin
from manager import Manager
from util import DATEFMT
from .system import SystemKeys

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

        # Parse the document as YAML
        parsed_yaml = yaml.load(yml)

        d = {}
        # For each k/v pair try to replace it if we need to
        for key, value in parsed_yaml.iteritems():
            # Check if we need can replace the entry with a YmlEntry
            # from our 'cache'
            entry = cls.entry(envid, key, default=None)
            # if not, create a new entry
            if entry is None:
                entry = cls(envid=envid, key=key)

            # Set its value. We need to have values
            # that can be JSON serialized later
            json_safe_value = value
            if isinstance(json_safe_value, date):
                json_safe_value = value.__str__()

            entry.value = json_safe_value
            # Add to the session
            session.add(entry)
            # And store it in the output dict
            d[key] = json_safe_value

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
        path = agent.tableau_data_dir
        if agent.path.basename(path) != "data":
            path = agent.path.join(path, "data")
        path = agent.path.join(path, "tabsvc", "config", "workgroup.yml")
        if not agent.displayname:
            location = agent.hostname + ' - ' + path
        else:
            location = agent.displayname + ' - ' + path
        timestamp = datetime.now().strftime(DATEFMT)
        contents = agent.filemanager.get(path)
        body = YmlEntry.sync(self.envid, contents)
        self.system.save(SystemKeys.YML_LOCATION, location)
        self.system.save(SystemKeys.YML_TIMESTAMP, timestamp)
        return body
