from sqlalchemy import Column, Integer, BigInteger, String, DateTime, func, or_
from sqlalchemy import ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.orm.exc import NoResultFound

import akiri.framework.sqlalchemy as meta

from manager import Manager
from mixin import BaseDictMixin

class FileEntry(meta.Base, BaseDictMixin):
    __tablename__ = 'files'

    fileid = Column(Integer, unique=True, nullable=False, primary_key=True)
    envid = Column(BigInteger, ForeignKey("environment.envid"))
    name = Column(String)
    file_type = Column(String)      # backup, ziplog, etc.
    username = Column(String)       # Tableau run-as user
    storage_type = Column(String)   # vol, cloud
    storageid = Column(BigInteger)  # volid or cloudid
    size = Column(BigInteger)
    auto = Column(Boolean)  # automatically requested/scheduled
    encrypted = Column(Boolean)  # whether or not it is encrypted
    creation_time = Column(DateTime, server_default=func.now())
    modification_time = Column(DateTime, server_default=func.now(), \
                               server_onupdate=func.current_timestamp())
    UniqueConstraint('envid', 'name')


class FileManager(Manager):

    STORAGE_TYPE_VOL = "vol"
    STORAGE_TYPE_CLOUD = "cloud"

    FILE_TYPE_BACKUP = "backup"
    FILE_TYPE_ZIPLOG = "ziplog"
    FILE_TYPE_WORKBOOK = "workbook"
    FILE_TYPE_DATASOURCE = "datasource"

    # FIXME: replace this with kwargs variant.
    def add(self, name, file_type, storage_type, storageid,
            size=0, auto=True, encrypted=False, username=None):
        # pylint: disable=too-many-arguments
        session = meta.Session()
        entry = FileEntry(envid=self.envid, name=name, file_type=file_type,
                          username=username, storage_type=storage_type,
                          storageid=storageid, size=size, auto=auto,
                          encrypted=encrypted)
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

        except NoResultFound:
            return None

    def find_by_id(self, fileid):
        try:
            return meta.Session.query(FileEntry).\
                filter(FileEntry.envid == self.envid).\
                filter(FileEntry.fileid == fileid).\
                one()

        except NoResultFound:
            return None

    @classmethod
    def find_by_name_envid(cls, envid, name):
        try:
            return meta.Session.query(FileEntry).\
                filter(FileEntry.envid == envid).\
                filter(FileEntry.name == name).\
                one()

        except NoResultFound:
            return None

    @classmethod
    def all(cls, envid, asc=True):
        query = meta.Session.query(FileEntry).\
            filter(FileEntry.envid == envid)
        if asc:
            query = query.order_by(FileEntry.creation_time.asc())
        else:
            query = query.order_by(FileEntry.creation_time.desc())
        return query.all()

    @classmethod
    def all_by_type(cls, envid, file_type, asc=True):
        query = meta.Session.query(FileEntry).\
            filter(FileEntry.envid == envid).\
            filter(FileEntry.file_type == file_type)
        if asc:
            query = query.order_by(FileEntry.creation_time.asc())
        else:
            query = query.order_by(FileEntry.creation_time.desc())
        return query.all()

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
