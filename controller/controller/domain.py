from datetime import datetime
from sqlalchemy import Column, String, BigInteger, DateTime, func, Boolean

# pylint: disable=import-error,no-name-in-module
from akiri.framework.ext.sqlalchemy import meta
# pylint: enable=import-error,no-name-in-module

from mixin import BaseMixin, BaseDictMixin

class Domain(meta.Base, BaseMixin, BaseDictMixin):
    __tablename__ = 'domain'

    domainid = Column(BigInteger, unique=True, nullable=False,
                           autoincrement=True, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)
    license_key = Column(String)
    systemid = Column(String)
    expiration_time = Column(DateTime)
    contact_time = Column(DateTime)
    trial = Column(Boolean)
    creation_time = Column(DateTime, server_default=func.now())
    modification_time = Column(DateTime, server_default=func.now(),
                                   server_onupdate=func.current_timestamp())

    defaults = [{'domainid':0, 'name':'default.local'}]

    def trial_days(self):
        if not self.trial:
            return None
        timedelta = self.expiration_time - datetime.now()
        if timedelta.days > 0:
            return timedelta.days
        return 0

    @classmethod
    def get_by_name(cls, name):
        # We expect the entry to exist, so allow a NoResultFound
        # exception to percolate up if the entry is not found.
        entry = meta.Session.query(Domain).\
            filter(Domain.name == name).one()
        return entry

    @classmethod
    def getone(cls):
        return meta.Session.query(Domain).one()
