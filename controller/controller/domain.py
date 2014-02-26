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
    domainname = Column(String, unique=True, nullable=False, \
      index=True)
    creation_time = Column(DateTime, server_default=func.now())
    modification_time = Column(DateTime, server_default=func.now(), \
      server_onupdate=func.current_timestamp())

    def __init__(self, domainname):
        self.domainname = domainname

class Domain(object):

    def __init__(self, server):
        self.server = server
        self.Session = sessionmaker(bind=meta.engine)

        # FIXME: Pre-production hack to ensure there is always
        #        a default domain
        session = self.Session()
        try:
            entry = session.query(DomainEntry).\
              filter(DomainEntry.domainname == 'default').one()
        except  NoResultFound, e:
            entry = DomainEntry('default')
            session.add(entry)
            session.commit()
            session.close()
        finally:
            session.close()
