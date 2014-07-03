from sqlalchemy import DateTime
from akiri.framework.ext.sqlalchemy import meta
from util import DATEFMT

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
                value = value.strftime(DATEFMT)
            elif not isinstance(value, (int, long)):
                value = str(value)
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

