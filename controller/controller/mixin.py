from sqlalchemy import DateTime
from akiri.framework.ext.sqlalchemy import meta
from util import DATEFMT

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
    
    @classmethod
    def populate(cls):
        session = meta.Session()
        entry = session.query(cls).first()
        if entry:
            return
        for d in cls.defaults:
            obj = cls(**d)
            session.add(obj)
        session.commit()
