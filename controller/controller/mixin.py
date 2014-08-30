from sqlalchemy import DateTime, func
from sqlalchemy.orm.exc import NoResultFound
from akiri.framework.ext.sqlalchemy import meta
from util import DATEFMT, utc2local

import os
import json

class BaseDictMixin(object):

    def todict(self, pretty=False, exclude=[]):
        if not isinstance(self, meta.Base):
            raise ProgrammingError("meta.Base instance required.");
        d = {}
        for c in self.__table__.columns:
            if c.name in exclude:
                continue
            value = getattr(self, c.name)
            if value is None:
                continue
            if isinstance(c.type, DateTime):
                try:
                    value = utc2local(value) # FIXME
                    value = value.strftime(DATEFMT)
                except AttributeError, e:
                     # It is possible this value has been set directly but
                     # not yet converted by the ORM.
                     # i.e. It is not a DateTime instance but something else
                     # that can be later converted to a DateTime instance.
                    value = str(value)
            elif not isinstance(value, (int, long)):
                value = unicode(value)
            name = pretty and c.name.replace('_', '-') or c.name
            d[name] = value
        return d

class BaseMixin(object):

    defaults = []
    defaults_filename = None
    
    @classmethod
    def populate(cls):
        session = meta.Session()
        entry = session.query(cls).first()
        if entry:
            return
        if not cls.defaults_filename is None:
            rows = cls.populate_from_file(cls.defaults_filename)
        else:
            rows = cls.defaults
        for d in rows:
            obj = cls(**d)
            session.add(obj)
        session.commit()

    @classmethod
    def populate_from_file(cls, filename):
        path = os.path.dirname(os.path.realpath(__file__)) + "/" + filename
  
        with open(path, "r") as f:
            rows = json.load(f)
            return rows['RECORDS']

    @classmethod
    def get_unique_by_keys(cls, keys, **kwargs):
        if 'default' in kwargs:
            default = kwargs['default']
            have_default = True
            del kwargs['default']
        else:
            have_default = False

        if kwargs:
            raise ValueError("Invalid kwargs: " + str(kwargs))
        
        query = meta.Session.query(cls)

        for key, value in keys.items():
            query = query.filter(getattr(cls, key) == value)

        try:
            entry = query.one()
        except NoResultFound, e:
            if have_default:
                return default
            raise ValueError("No such value: " + str(keys))
        return entry


    @classmethod
    def get_all_by_keys(cls, keys, order_by=[], limit=None):
        query = meta.Session.query(cls)
        for key, value in keys.items():
            query = query.filter(getattr(cls, key) == value)
        if isinstance(order_by, basestring):
            order_by = [order_by]
        for clause in order_by:
            query = query.order_by(clause)
        if not limit is None:
            query = query.limit(limit)
        return query.all()

    @classmethod
    def max(cls, column, filters={}, default=None):
        query = meta.Session().query(func.max(getattr(cls, column)))
        for key, value in filters.items():
            query = query.filter(getattr(cls, key) == value)
        value = query.scalar()
        if value is None:
            return default
        return value

    @classmethod
    def count(cls, filters={}):
        query = meta.Session().query(cls)
        for key, value in filters.items():
            query = query.filter(getattr(cls, key) == value)
        return query.count()


class OnlineMixin(object):

    @classmethod
    def exists_in_envid(cls, envid):
        try:
            entry = meta.Session.query(cls).\
                filter(cls.envid == envid).one()
            return True
        except NoResultFound, e:
            return False
