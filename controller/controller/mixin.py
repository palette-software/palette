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

class BaseMixin(object):

    defaults = []
    
    @classmethod
    def populate(cls):
        session = meta.Session()
        entry = session.query(cls).first()
        if entry:
            return
        import pdb; pdb.set_trace();
        for d in cls.defaults:
            obj = cls(**d)
            session.add(obj)
        session.commit()
