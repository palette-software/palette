""" Module represent the 'system' table - a key/value settings store for a
particular environment. """
# pylint: enable=missing-docstring,relative-import
from UserDict import DictMixin

from sqlalchemy import Column, String, BigInteger, DateTime
from sqlalchemy import func
from sqlalchemy.schema import ForeignKey

import akiri.framework.sqlalchemy as meta

from ..mixin import BaseMixin, BaseDictMixin
from ..manager import Manager
from ..util import str2bool

from .keys import SystemKeys
from .defaults import DEFAULTS

def base_data_type(value):
    """ Return the simple data type (without translation) """
    if value is None or isinstance(value, basestring):
        return str
    # Must test for bool before int since bool is also an int.
    if isinstance(value, bool):
        return bool
    if isinstance(value, int):
        return int
    return dict

def data_type(key):
    """ Return the data type for the specified key using the DEFAULTS dict. """
    value = DEFAULTS[key]
    result = base_data_type(value)
    if result != dict:
        return result
    if 'data-type' in value:
        return value['data-type']
    return base_data_type(value['value'])

def default(key):
    """ Return the default value for key - including translating dicts """
    value = DEFAULTS[key]
    if base_data_type(value) == dict:
        if 'value' in value:
            return value['value']
        else:
            return None
    return value

def cast(key, value):
    """ Find the native type of key in DEFAULTS and return 'value'
    converted to that type."""
    if value is None:
        return None
    datatype = data_type(key)
    if datatype == bool:
        return str2bool(value)
    return datatype(value)

class SystemEntry(meta.Base, BaseMixin, BaseDictMixin):
    """ An entry in the system table """
    __tablename__ = 'system'

    envid = Column(BigInteger, ForeignKey("environment.envid"),
                   primary_key=True)
    key = Column(String, unique=True, nullable=False, primary_key=True)
    value = Column(String)
    creation_time = Column(DateTime, server_default=func.now())
    modification_time = Column(DateTime, server_default=func.now(),
                               onupdate=func.current_timestamp())

    def typed(self):
        """ Return the value explicity cast to the correct data type. """
        try:
            return cast(self.key, self.value)
        except ValueError:
            raise

    @classmethod
    def get_by_key(cls, envid, key, **kwargs):
        """ Return the value for a system key in a particular environment. """
        filters = {'envid':envid, 'key':key}
        return cls.get_unique_by_keys(filters, **kwargs)

    @classmethod
    def get_all(cls, envid):
        """ Return all system table entries for a particular enviroment. """
        filters = {'envid':envid}
        return cls.get_all_by_keys(filters)


class SystemMixin(object):
    """ Mixin class for objects that deal with the system table.
    This mixin assumes that the instance behaves like a dict(). """

    def delete(self, key):
        """ Deprecated: instead use the below line directly. """
        del self[key]

    def save(self, key, value):
        """ Update the database and commit """
        self[key] = value
        meta.commit()

class SystemManager(Manager, DictMixin, SystemMixin):
    """ Non-caching manager for the system table.  It can behave like a dict
    with get/set performaning the database operation.  """

    def entry(self, key, **kwargs):
        """ Return the SystemEntry for this key. """
        try:
            return SystemEntry.get_by_key(self.envid, key, **kwargs)
        except ValueError:
            return None

    def __getitem__(self, key):
        """ Returns the value of the system key from the database or the
        keys default if not overridden in the database."""
        entry = self.entry(key)
        if entry:
            return cast(key, entry.value)
        if key not in DEFAULTS:
            raise KeyError("Invalid system key : " + key)
        value = DEFAULTS[key]
        if isinstance(value, dict):
            return value['value']
        return value

    def __setitem__(self, key, value):
        """ Updates the database row for key with 'value'.
        NOTE: does *not* commit the database.
        """
        # This cast implicity checks if value is correctly typed.
        value = cast(key, value)
        session = meta.Session()
        entry = SystemEntry(envid=self.envid, key=key, value=str(value))
        session.merge(entry)

    def __delitem__(self, key):
        """ Delete a row from the system table. """
        SystemEntry.delete(filters={'envid':self.envid, 'key':key})

    def todict(self):
        """ Import the system table as a dict (used by event_control) """
        data = {}
        for entry in SystemEntry.get_all(self.envid):
            try:
                data[entry.key] = entry.typed()
            except ValueError:
                raise
        return data

    @classmethod
    def populate(cls):
        """ Import default values into an empty system table. """
        session = meta.Session()
        entry = session.query(SystemEntry).first()
        if entry:
            return
        for key in DEFAULTS:
            # FIXME: eventually remove constant
            value = DEFAULTS[key]
            if isinstance(value, dict):
                if 'populate' in dict and not dict['populate']:
                    continue
                value = value['value']
            if value is None:
                continue
            entry = SystemEntry(envid=1, key=key, value=str(value))
            session.add(entry)
        session.commit()
