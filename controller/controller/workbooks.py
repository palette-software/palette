import time
from sqlalchemy import Column, BigInteger, String, DateTime, func
from sqlalchemy.schema import ForeignKey

from akiri.framework.ext.sqlalchemy import meta

class WorkbookEntry(meta.Base):
    __tablename__ = "workbooks"

    workbookid = Column(BigInteger, unique=True, nullable=False, \
                                   autoincrement=True, primary_key=True)

    domainid = Column(BigInteger, ForeignKey("domain.domainid"))
    name = Column(String)
    summary = Column(String)
    color = Column(String)

class WorkbookManager(object):

    def __init__(self, domainid):
        self.domainid = domainid

    def add(self, title, name, summary, color):
        session = meta.Session()
        entry = workbookEntry(domainid=self.domainid, name=name,
                                            summary=summary, color=color)
        session.add(entry)
        session.commit()

    def populate(self):
        entry = meta.Session.query(WorkbookEntry).first()

        if entry:
            return

        entry = WorkbookEntry()
        entry.domainid = self.domainid
        entry.name = "Eastern Region Quarterly Sales Report.twbx"
        entry.summary = "John Abdo"
        entry.color = 'grey'
        meta.Session.add(entry)

        entry = WorkbookEntry()
        entry.domainid = self.domainid
        entry.name = "Restoration initializated on Xepler Production Server #2"
        entry.summary = "Bixly Production Server"
        entry.color = 'grey'
        meta.Session.add(entry)
        meta.Session.commit()

        entry = WorkbookUpdatesEntry()
        entry.domainid = self.domainid
        entry.workbookid = 1
        entry.name = "John Abdo"
        entry.timestamp = "5:30 PM on May 1, 2014"
        entry.url = "#"
        meta.Session.add(entry)

        entry = WorkbookUpdatesEntry()
        entry.domainid = self.domainid
        entry.workbookid = 1
        entry.name = "Matthew Laue"
        entry.timestamp = "2:17 PM on April 14, 2014"
        entry.url = "#"
        meta.Session.add(entry)

        entry = WorkbookUpdatesEntry()
        entry.domainid = self.domainid
        entry.workbookid = 2
        entry.name = "Bixly Production Server has completed a lorem ipsum text placeholder words. Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum"

        entry.timestamp = "3:27 PM on May 11, 2014"
        entry.url = "#"
        meta.Session.add(entry)

        meta.Session.commit()

class WorkbookUpdatesEntry(meta.Base):
    __tablename__ = "workbooks_updates"

    workbook_updates_id = Column(BigInteger, unique=True, nullable=False, \
                                   autoincrement=True, primary_key=True)

    domainid = Column(BigInteger, ForeignKey("domain.domainid"))
    workbookid = Column(BigInteger, ForeignKey("workbooks.workbookid"))
    name = Column(String)
    timestamp = Column(String)
    url = Column(String)

class WorkbookUpdatesManager(object):

    def __init__(self, domainid):
        self.domainid = domainid

    def add(self, workbookid, name, timestamp, url):
        session = meta.Session()
        entry = workbookEntry(domainid=self.domainid, name=name,
                                        timestamp=timestamp, url=url)
        session.add(entry)
        session.commit()
