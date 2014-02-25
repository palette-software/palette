import sqlalchemy
from sqlalchemy import Column, String, BigInteger, DateTime, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

import meta

class DomainEntry(meta.Base):
    __tablename__ = 'domain'

    domainid =  Column(BigInteger, unique=True, nullable=False, \
      autoincrement=True, primary_key=True)
    domain = Column(String, unique=True, nullable=False, \
      index=True)
    creation_time = Column(DateTime, server_default=func.now(), \
      onupdate=func.current_timestamp())

    def __init__(self, domain):
        self.domain = domain

class Domain(object):

    def __init__(self, server):
        self.server = server
        self.Session = sessionmaker(bind=meta.engine)

        # FIXME: pre-production hack to ensure there is always
        #        a default domain
        session = self.Session()
        try:
            entry = session.query(DomainEntry).\
              filter(DomainEntry.domain == 'default').one()
        except  NoResultFound, e:
            entry = DomainEntry('default')
            session.add(entry)
            session.commit()
            session.close()
        finally:
            session.close()
