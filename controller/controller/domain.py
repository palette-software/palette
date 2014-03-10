import sqlalchemy
from sqlalchemy import Column, String, BigInteger, DateTime, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound

import meta

class DomainEntry(meta.Base):
    __tablename__ = 'domain'

    domainid =  Column(BigInteger, unique=True, nullable=False, \
      autoincrement=True, primary_key=True)
    domainname = Column(String, unique=True, nullable=False, \
      index=True)
    creation_time = Column(DateTime, server_default=func.now())
    modification_time = Column(DateTime, server_default=func.now(), \
      server_onupdate=func.current_timestamp())

    def __init__(self, domainname):
        self.domainname = domainname

class Domain(object):

    def __init__(self, Session=None):
        if Session is None:
            self.Session = sessionmaker(bind=meta.engine)
        else:
            self.Session = Session

    def add(self, name):
        session = self.Session()
        # FIXME: Can we do a merge rather than a query followed by an add?
        try:
            entry = session.query(DomainEntry).\
              filter(DomainEntry.domainname == name).one()
        except  NoResultFound, e:
            entry = DomainEntry(name)
            session.add(entry)
            session.commit()
        finally:
            session.close()

    def id_by_name(self, name):
        entry = Domain.get_by_name(name, Session=self.Session)
        return entry.domainid

    @classmethod
    def get_by_name(cls, name, Session=None):
        if Session is None:
            Session = sessionmaker(bind=meta.engine)
        session = Session()

        # We expect the entry to exist, so allow a NoResultFound
        # exception to percolate up if the entry is not found.
        entry = session.query(DomainEntry).\
            filter(DomainEntry.domainname == name).one()

        session.close()

        return entry
