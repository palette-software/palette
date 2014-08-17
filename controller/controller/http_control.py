from sqlalchemy import Column, String, Integer, BigInteger, DateTime
from sqlalchemy import func

from akiri.framework.ext.sqlalchemy import meta
from mixin import BaseMixin, BaseDictMixin

class HttpControl(meta.Base, BaseMixin):
    __tablename__ = "http_control"

    hcid = Column(BigInteger, unique=True, nullable=False,
                  autoincrement=True, primary_key=True)

    status = Column(BigInteger, unique=True, nullable=False)
    level = Column(Integer, nullable=False, default=1)
    excludes = Column(String)
    creation_time = Column(DateTime, server_default=func.now())
    modification_time = Column(DateTime, server_default=func.now(),
                               onupdate=func.current_timestamp())

    defaults = [{'status':500}]

    @classmethod
    def all(cls):
        return meta.Session.query(HttpControl).\
            filter(HttpControl.level > 0).\
            all()

    @classmethod
    def info(cls):
        d = {}
        for entry in cls.all():
            if entry.excludes:
                excludes = entry.excludes.replace(',', ' ')
                d[entry.status] = excludes.strip()
            else:
                d[entry.status] = []
        return d
