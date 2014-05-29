from akiri.framework.ext.sqlalchemy import meta

class BaseDictMixin(object):

    def todict(self, pretty=False, exclude=[]):
        if not isinstance(self, meta.Base):
            raise ProgrammingError("meta.Base instance required.");
        d = {}
        for c in self.__table__.columns:
            if c.name in exclude:
                continue
            value = str(getattr(self, c.name))
            name = pretty and c.name.replace('_', '-') or c.name
            d[name] = value
        return d
