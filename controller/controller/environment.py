from sqlalchemy import Column, BigInteger, String, DateTime, func
from sqlalchemy.schema import ForeignKey

import akiri.framework.sqlalchemy as meta

from mixin import BaseMixin

class Environment(meta.Base, BaseMixin):
    __tablename__ = 'environment'

    envid = Column(BigInteger, unique=True, nullable=False, \
                   autoincrement=True, primary_key=True)
    domainid = Column(BigInteger,
                      ForeignKey("domain.domainid", onupdate='CASCADE'))
    name = Column(String, unique=True, nullable=False, index=True)
    creation_time = Column(DateTime, server_default=func.now())
    modification_time = Column(DateTime, server_default=func.now(), \
                               server_onupdate=func.current_timestamp())

    defaults = [{'envid':1, 'domainid':0, 'name':'Production'}]

    @classmethod
    def get(cls):
        # FIXME: Currently only allow a single env
        # We expect the entry to exist, so allow a NoResultFound
        # exception to percolate up if the entry is not found.
        return meta.Session.query(Environment).one()
