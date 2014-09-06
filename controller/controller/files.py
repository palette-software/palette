from mixin import BaseDictMixin
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, func, or_
from sqlalchemy import ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound

from akiri.framework.ext.sqlalchemy import meta

from agent import Agent
from agentinfo import AgentVolumesEntry

from manager import Manager
from util import DATEFMT

class FileEntry(meta.Base):
    __tablename__ = 'files'

    fileid = Column(Integer, unique=True, nullable=False, primary_key=True)
    envid = Column(BigInteger, ForeignKey("environment.envid"))
    name = Column(String)
    file_type = Column(String)      # backup, ziplog, etc.
    storage_type = Column(String)   # vol, cloud
    storageid = Column(BigInteger)  # volid or cloudid
    size = Column(BigInteger)
    auto = Column(Boolean)  # automatically requested/scheduled
    encrypted = Column(Boolean)  # whether or not it is encrypted
    creation_time = Column(DateTime, server_default=func.now())
    modification_time = Column(DateTime, server_default=func.now(), \
                               server_onupdate=func.current_timestamp())
    UniqueConstraint('envid', 'name')

    # FIXME: make this a mixin
    def todict(self, pretty=False):
        d = { 'fileid': self.fileid,
              'storagetype': self.storage_type,
              'storageid': self.storageid,
              'size': self.size,
              'auto': self.auto,
              'name': self.name}
        if pretty:
            d['creation-time'] = self.creation_time.strftime(DATEFMT)
            d['modification-time'] = self.modification_time.strftime(DATEFMT)
        else:
            d['creation_time'] = str(self.creation_time)
            d['modification_time'] = str(self.modification_time)
        return d

class FileManager(Manager):

    STORAGE_TYPE_VOL="vol"
    STORAGE_TYPE_CLOUD="cloud"

    FILE_TYPE_BACKUP="backup"
    FILE_TYPE_ZIPLOG="ziplog"
    FILE_TYPE_WORKBOOK="workbook"

    def add(self, name, file_type, storage_type, storageid,
                                        size=0, auto=True, encrypted=False):
        session = meta.Session()
        entry = FileEntry(envid=self.envid, name=name, file_type=file_type,
                          storage_type=storage_type, storageid=storageid, size=size,
                          auto=auto, encrypted=encrypted)
        session.add(entry)
        session.commit()
        return entry

    def remove(self, fileid):
        session = meta.Session()
        session.query(FileEntry).\
            filter(FileEntry.envid == self.envid).\
            filter(FileEntry.fileid == fileid).\
            delete()
        session.commit()

    def find_by_name(self, name):
        try:
            return meta.Session.query(FileEntry).\
                filter(FileEntry.envid == self.envid).\
                filter(FileEntry.name == name).\
                one()

        except NoResultFound, e:
            return None

    @classmethod
    def find_by_name_envid(cls, envid, name):
        try:
            return meta.Session.query(FileEntry).\
                filter(FileEntry.envid == envid).\
                filter(FileEntry.name == name).\
                one()

        except NoResultFound, e:
            return None

    @classmethod
    def all(cls, envid, asc=True):
        q = meta.Session.query(FileEntry)
        if asc:
            q = q.order_by(FileEntry.creation_time.asc())
        else:
            q = q.order_by(FileEntry.creation_time.desc())
        return q.all()

    @classmethod
    def all_by_type(cls, envid, file_type, asc=True):
        q = meta.Session.query(FileEntry).\
            filter(FileEntry.file_type == file_type)
        if asc:
            q = q.order_by(FileEntry.creation_time.asc())
        else:
            q = q.order_by(FileEntry.creation_time.desc())
        return q.all()

    @classmethod
    def find_by_auto_envid(cls, envid, file_type):
        """Return all auto/scheduled files in oldest-to-newest order."""
        return meta.Session.query(FileEntry).\
            filter(FileEntry.envid == envid).\
            filter(FileEntry.file_type == file_type).\
            filter(or_(FileEntry.auto == True, FileEntry.auto == None)).\
            order_by(FileEntry.creation_time).\
            all()

    @classmethod
    def find_by_non_auto_envid(cls, envid, file_type):
        """Return all user-requested files in oldest-to-newest order."""
        return meta.Session.query(FileEntry).\
            filter(FileEntry.envid == envid).\
            filter(FileEntry.file_type == file_type).\
            filter(FileEntry.auto == False).\
            order_by(FileEntry.creation_time).\
            all()
