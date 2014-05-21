import time

from sqlalchemy import Column, BigInteger, String, DateTime, func
from sqlalchemy.schema import ForeignKey

from akiri.framework.ext.sqlalchemy import meta

class ExtractsEntry(meta.Base):
    __tablename__ = "extracts"

    extractid = Column(BigInteger, unique=True, nullable=False, \
                                   autoincrement=True, primary_key=True)

    domainid = Column(BigInteger, ForeignKey("domain.domainid"))
    name = Column(String)
    summary = Column(String)
    description = Column(String)
    color = Column(String)

class ExtractManager(object):

    def __init__(self, domainid):
        self.domainid = domainid

    def add(self, name, summary, description, color):
        session = meta.Session()
        entry = extractEntry(domainid=self.domainid, name=name,
            summary=summary, description=description, color=color)
        session.add(entry)
        session.commit()
