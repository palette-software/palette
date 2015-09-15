import sqlalchemy
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, func, or_
from sqlalchemy import ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.orm.exc import NoResultFound

import akiri.framework.sqlalchemy as meta

from agent import AgentVolumesEntry
from manager import Manager
from mixin import BaseDictMixin
from util import failed

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
        # envid is technically not required
        session = meta.Session()
        session.query(FileEntry).\
            filter(FileEntry.envid == self.envid).\
            filter(FileEntry.fileid == fileid).\
            delete()
        session.commit()

    def remove_file_by_id(self, fileid):
        """Removes the file from disk or cloud.
           When done, removes the row from the files table.
        """
        file_entry = self.server.files.find_by_id(fileid)
        if not file_entry:
            self.log.info(
                    "remove_file fileid %d disappeared, or was never added.",
                    fileid)
            return

        body = self.delfile_by_entry(file_entry)
        if failed(body):
            self.log.info(
                "remove_file failed to delete fileid %d", fileid)
        else:
            self.log.debug(
                "remove_file deleted fileid %d", fileid)

    def delfile_by_entry(self, file_entry):
        """Delete a file, wherever it is
            Argument:
                    file_entry   The file entry.
        """
        # pylint: disable=too-many-return-statements

        # Delete a file from the cloud
        if file_entry.storage_type == FileManager.STORAGE_TYPE_CLOUD:
            try:
                self.server.cloud.delete_cloud_file_by_file_entry(file_entry)
            except IOError as ex:
                return {'error': str(ex)}
            try:
                self.remove(file_entry.fileid)
            except sqlalchemy.orm.exc.NoResultFound:
                return {'error': ("fileid %d not found: name=%s cloudid=%d" % \
                        (file_entry.fileid, file_entry.name,
                        file_entry.storageid))}
            return {}

        # Delete a file from an agent.
        vol_entry = AgentVolumesEntry.get_vol_entry_by_volid(
                                                    file_entry.storageid)
        if not vol_entry:
            return {"error": "volid not found: %d" % file_entry.storageid}

        target_agent = None
        agents = self.server.agentmanager.all_agents()
        for key in agents.keys():
            self.server.agentmanager.lock()
            if not agents.has_key(key):
                self.log.info(
                    "copy_cmd: agent with conn_id %d is now " + \
                    "gone and won't be checked.", key)
                self.server.agentmanager.unlock()
                continue
            agent = agents[key]
            self.server.agentmanager.unlock()

            if agent.agentid == vol_entry.agentid:
                target_agent = agent
                break

        if not target_agent:
            return {'error': "Agentid %d not connected." % vol_entry.agentid}

        file_full_path = file_entry.name
        self.log.debug("delfile_cmd: Deleting path '%s' on agent '%s'",
                       file_full_path, target_agent.displayname)

        body = self.delete_vol_file(target_agent, file_full_path)

        # We remove the entry from the files table regardless of
        # whether or not the file was successfully removed:
        # If it failed to remove, it was probably because it was already
        # gone.
        try:
            self.remove(file_entry.fileid)
        except sqlalchemy.orm.exc.NoResultFound:
            return {'error': ("fileid %d not found: name=%s agent=%s" % \
                    (file_entry.fileid, file_full_path,
                        target_agent.displayname))}
        return body

    def delete_vol_file(self, agent, source_fullpathname):
        """Delete a file, check the error, and return the body result.
           Note: Does not remove the entry from the files table.
           If that is needed, that must be done by the caller."""
        self.log.debug("Removing file '%s'", source_fullpathname)

        # Verify file exists.
        try:
            exists_body = agent.filemanager.filesize(source_fullpathname)
        except IOError as ex:
            self.log.info("filemanager.filesize('%s') failed: %s",
                            source_fullpathname, str(ex))
            return {'error': str(ex)}

        if failed(exists_body):
            self.log.info("filemanager.filesize('%s') error: %s",
                            source_fullpathname, str(exists_body))
            return exists_body

        # Remove file.
        try:
            remove_body = agent.filemanager.delete(source_fullpathname)
        except IOError as ex:
            self.log.info("filemanager.delete('%s') failed: %s",
                            source_fullpathname, str(ex))
            return {'error': str(ex)}

        return remove_body

    def find_by_name(self, name):
        try:
            return meta.Session.query(FileEntry).\
                filter(FileEntry.envid == self.envid).\
                filter(FileEntry.name == name).\
                one()

        except NoResultFound:
            return None

    def find_by_id(self, fileid):
        """ Return a file by id """
        # NOTE: the envid is used as a sanity check; fileid is globally unique.
        try:
            return meta.Session.query(FileEntry).\
                filter(FileEntry.envid == self.envid).\
                filter(FileEntry.fileid == fileid).\
                one()

        except NoResultFound:
            return None

    @classmethod
    def find_by_fileid(cls, fileid):
        """ Find a FileEntry by unique id.
        NOTE: 'fileid' is unique across environments.
        """
        try:
            return meta.Session.query(FileEntry).\
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
    def all_by_type(cls, envid, file_type, asc=True, limit=None):
        query = meta.Session.query(FileEntry).\
            filter(FileEntry.envid == envid).\
            filter(FileEntry.file_type == file_type)
        if asc:
            query = query.order_by(FileEntry.creation_time.asc())
        else:
            query = query.order_by(FileEntry.creation_time.desc())
        if not limit is None:
            query = query.limit(limit)
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
