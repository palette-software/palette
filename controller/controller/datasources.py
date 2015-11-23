import logging

from sqlalchemy import Column, String, DateTime, Boolean, Integer, BigInteger
from sqlalchemy import UniqueConstraint, Text
from sqlalchemy.schema import ForeignKey
from sqlalchemy.orm import relationship, backref, deferred
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import func, or_

import akiri.framework.sqlalchemy as meta

from odbc import ODBC

from archive_mixin import ArchiveUpdateMixin, ArchiveException, ArchiveError
from mixin import BaseMixin, BaseDictMixin
from cache import TableauCacheManager #FIXME
from manager import synchronized
from util import failed
from .system import SystemKeys

from diskcheck import DiskCheck, DiskException
from event_control import EventControl
from files import FileManager

from sites import Site
from projects import Project

logger = logging.getLogger()


# NOTE: system_user_id is maintained in two places.  This is not ideal from
# a db design perspective but makes the find-by-current-owner code clearer.
class DataSourceEntry(meta.Base, BaseMixin, BaseDictMixin):

    __tablename__ = 'datasources'

    dsid = Column(BigInteger, primary_key=True)
    envid = Column(Integer, ForeignKey("environment.envid"), nullable=False)
    system_user_id = Column(Integer)        # Added in 1.6: only in paldb
    id = Column(Integer, nullable=False)
    name = Column(String)
    repository_url = Column(String)
    owner_id = Column(Integer, nullable=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    project_id = Column(Integer)
    size = Column(BigInteger)
    lock_version = Column(Integer)
    state = Column(String)
    db_class = Column(String)
    db_name = Column(String)
    table_name = Column(String)
    site_id = Column(Integer)
    repository_data_id = Column(BigInteger)
    repository_extract_data_id = Column(BigInteger)
    embedded = Column(String)
    incremental_extracts = Column(Boolean)
    refreshable_extracts = Column(Boolean)
    data_engine_extracts = Column(Boolean)
    extracts_refreshed_at = Column(DateTime)

    # Added in 1.5:
    first_published_at = Column(DateTime)
    connectable = Column(Boolean)
    is_hierarchical = Column(Boolean)
    extracts_incremented_at = Column(DateTime)

    luid = Column(String)
    asset_key_id = Column(Integer)
    document_version = Column(String)

    # In Tableau 9.x, but not in Tableau 8.3.10.
    description = Column(String)

    __table_args__ = (UniqueConstraint('envid', 'site_id', 'project_id',
                                           'luid'),)

    def __getattr__(self, name):
        if name == 'site':
            return Site.get_name_by_id(self.envid, self.site_id)
        elif name == 'project':
            return Project.get_name_by_id(self.envid, self.project_id)
        raise AttributeError(name)

    @classmethod
    def get(cls, envid, site_id, project_id, luid, **kwargs):
        keys = {'envid':envid, 'site_id':site_id,
            'project_id': project_id,
            'luid': luid}
        return cls.get_unique_by_keys(keys, **kwargs)

    @classmethod
    def get_newest_by_id(cls, envid, datasource_id):
        rows = cls.get_all_by_keys({'envid': envid, 'id': datasource_id},
                                order_by=[DataSourceEntry.updated_at.desc()],
                                limit=1)
        if not rows:
            return None
        return rows[0]

    @classmethod
    def get_last_updated_at(cls, envid):
        """Returns the most recent 'updated_at' value for the table,
           if it exists, or None if the table is empty."""

        value = cls.max('updated_at', filters={'envid':envid})
        if value is None:
            return None
        return str(value)

class DataSourceUpdateEntry(meta.Base, BaseMixin, BaseDictMixin):
    __tablename__ = "datasource_updates"

    dsuid = Column(BigInteger, unique=True, nullable=False, \
                  autoincrement=True, primary_key=True)
    dsid = Column(BigInteger,
                  ForeignKey("datasources.dsid", ondelete='CASCADE'))
    revision = Column(String, nullable=False)
    fileid_tds = Column(Integer, ForeignKey("files.fileid", ondelete='CASCADE'))
    fileid_tdsx = Column(Integer,
                         ForeignKey("files.fileid", ondelete='CASCADE'))
    timestamp = Column(DateTime, nullable=False)
    system_user_id = Column(Integer)
    url = Column(String)  # FIXME: make this unique.
    note = Column(String)
    tds = deferred(Column(Text))    # the contents of the .tds file

    # NOTE: system_user_id is not a foreign key to avoid load dependencies.

    datasource = relationship('DataSourceEntry', \
        backref=backref('updates',
                        order_by='desc(DataSourceUpdateEntry.revision)')
    )

    __table_args__ = (UniqueConstraint('dsid', 'revision'),)

    @classmethod
    def get(cls, dsid, revision, **kwargs):
        return cls.get_unique_by_keys({'dsid': dsid,
                                       'revision': revision},
                                      **kwargs)
    @classmethod
    def get_by_id(cls, dsuid, **kwargs):
        return cls.get_unique_by_keys({'dsuid': dsuid}, **kwargs)

    @classmethod
    def get_by_url(cls, url, **kwargs):
        return cls.get_unique_by_keys({'url': url}, **kwargs)

class DataSourceManager(TableauCacheManager, ArchiveUpdateMixin):
    NAME = 'datasource'
    PCMD = 'ptdsx'

    def __init__(self, server):
        super(DataSourceManager, self).__init__(server)

    # really sync *and* load
    @synchronized('datasource')
    def load(self, agent):
        # pylint: disable=too-many-locals

        envid = self.server.environment.envid


        stmt = \
            'SELECT id, name, repository_url, owner_id,' +\
            ' created_at, updated_at, project_id,' +\
            ' size, lock_version, state, db_class,' +\
            ' db_name, table_name, site_id, revision,' +\
            ' repository_data_id, repository_extract_data_id,' +\
            ' embedded, incrementable_extracts, refreshable_extracts,' +\
            ' first_published_at, connectable, is_hierarchical,' +\
            ' extracts_incremented_at, luid, asset_key_id ' +\
            'FROM datasources'

        session = meta.Session()

        last_updated_at = DataSourceEntry.get_last_updated_at(envid)
        if last_updated_at:
            stmt += " WHERE updated_at > '" + last_updated_at + "'"

        data = agent.odbc.execute(stmt)

        updates = []

        if 'error' in data or '' not in data:
            logger.debug("datasources load: bad data: %s", str(data))
            return data

        logger.debug(data)

        # Get users only if needed
        users = None

        for odbcdata in ODBC.load(data):
            name = odbcdata.data['name']
            revision = odbcdata.data['revision']
            site_id = odbcdata.data['site_id']
            project_id = odbcdata.data['project_id']
            luid = odbcdata.data['luid']

            dse = DataSourceEntry.get(envid, site_id, project_id, luid,
                                      default=None)
            if dse is None:
                dse = DataSourceEntry(envid=envid, site_id=site_id,
                                    project_id=project_id, luid=luid)
                session.add(dse)

            # NOTE: id is updated with each revision.
            odbcdata.copyto(dse, excludes=['revision'])

            if not users:
                users = self.load_users(agent)
            system_user_id = users.get(dse.site_id, dse.owner_id)
            dse.system_user_id = system_user_id

            # must commit here so that update foreign keys work.
            session.commit()

            dsu = DataSourceUpdateEntry.get(dse.dsid,
                                          revision,
                                          default=None)
            if not dsu:
                # The updated_at time is the publish time.
                dsu = DataSourceUpdateEntry(dsid=dse.dsid,
                                          revision=revision,
                                          system_user_id=system_user_id,
                                          timestamp=dse.updated_at,
                                          url='')
                session.add(dsu)
                updates.append(dsu)

            logger.debug("datasource update '%s', revision %s",
                            name, revision)

        session.commit()

        prune_count = self._prune_missed_revisions()

        if not self.system[SystemKeys.DATASOURCE_RETAIN_COUNT]:
            result = {u'disabled':
                      'Datasource Archives are not enabled. Will not archive.'}
        elif not self.cred_check():
            result = {u'error':
                      'Can not load datasources: missing credentials.'}
        else:
            # Second pass - build the archive files.
            result = self._archive_updates(agent, updates)

        result[u'schema'] = self.schema(data)
        result[u'updates-new'] = len(updates)
        result[u'updates-missed'] = prune_count

        return result

    def _prune_missed_revisions(self):
        """Remove rows from datasource_updates that we didn't manage to
           archive.  It may be due to bad credentials, failed tabcmd, etc.
           Returns:
                count of updates pruned.
        """

        stmt = "delete from datasource_updates where " + \
                "(dsid, timestamp) not in "+ \
                    "(select dsid, max(timestamp) "+ \
                    "from datasource_updates where url='' " + \
                    "group by dsid) " + \
                    "and url='';"

        connection = meta.get_connection()
        result = connection.execute(stmt)
        connection.close()

        if result.rowcount:
            logger.debug("datasource _prune_missed_revisions pruned %d",
                           result.rowcount)

        return result.rowcount

    def _retain_some(self):
        """Retain only the configured number of datasource versions.
            Returns:
                    The number of archive versions removed.
        """

        retain_count = self.system[SystemKeys.DATASOURCE_RETAIN_COUNT]
        if not retain_count or retain_count == -1:
            return 0

        removed_count = 0

        session = meta.Session()
        # List of datasources that have excess archived versions:
        #   [(dsid, total-count), ...]
        # Note we select only successfully archived datasource versions
        # (url != '').  We don't want want to count unsuccessfully
        # archived versions in the count of how many we have.
        results = session.query(DataSourceUpdateEntry.dsid, func.count()).\
                  filter(DataSourceUpdateEntry.url != '').\
                  group_by(DataSourceUpdateEntry.dsid).\
                  having(func.count() > retain_count).\
                  all()

#        logger.debug("datasources _retain_some len: %d, results: %s",
#                                                len(results), str(results))

        for result in results:
            # Get list of old datasource archive entries to delete
            rows = session.query(DataSourceUpdateEntry).\
                    filter(DataSourceUpdateEntry.dsid == result[0]).\
                    filter(DataSourceUpdateEntry.url != '').\
                    order_by(DataSourceUpdateEntry.timestamp.asc()).\
                    limit(result[1] - retain_count).\
                    all()

            for row in rows:
                # We have to remove the DataSourceUpdateEntry first
                # due to the foreign key constraint in files pointing to it.
                session.query(DataSourceUpdateEntry).\
                            filter(DataSourceUpdateEntry.dsuid == row.dsuid).\
                            delete()
                session.commit()

                self.server.files.remove_file_by_id(row.fileid_tds)
                if row.fileid_tdsx:
                    self.server.files.remove_file_by_id(row.fileid_tdsx)

                # Fixme: We could increment only if it successfully deleted.
                removed_count += 1

        return removed_count

    @synchronized('datasource.fixup')
    def fixup(self, agent):
        if not self.system[SystemKeys.DATASOURCE_RETAIN_COUNT]:
            logger.debug("Datasource archives are disabled. Fixup not done.")
            return {u'disabled':
                    'Datasource Archives are not enabled.  Fixup not done.'}

        session = meta.Session()

        # potentially serveral thousand?
        updates = session.query(DataSourceUpdateEntry).\
                  filter(or_(DataSourceUpdateEntry.url == "",
                         DataSourceUpdateEntry.url == None)).\
                         all()

        return self._archive_updates(agent, updates)

    def _archive_updates(self, agent, updates):
        """Attempt to archive datasources from DataSourceUpdate rows."""

        session = meta.Session()

        count = 0

        logger.debug("Datasource Archive update count: %d", len(updates))

        for update in updates:
            if not self.system[SystemKeys.DATASOURCE_RETAIN_COUNT]:
                logger.info(
                          "Datasource Archive disabled during fixup." + \
                          "  Exiting for now.")
                break

            if not self.server.odbc_ok():
                logger.info("Datasource Archive Fixup: Archive build " + \
                          "stopping due to current state")
                break

            logger.debug("Datasource Archive update refresh dsid %d",
                           update.dsid)

            session.refresh(update)
            try:
                self._archive_ds(agent, update)
            except ArchiveException as ex:
                if ex.value == ArchiveError.BAD_CREDENTIALS:
                    msg = "datasource _archive_updates: tabcmd failed due " + \
                          "to bad credentials. " + \
                          "Skipping any remaining datasource updates now."
                    logger.info(msg)
                    break
                else:
                    raise   # should never happen
            count += 1

        # Retain only configured number of versions
        if count:
            retain_removed_count = self._retain_some()
        else:
            retain_removed_count = 0

        return {u'status': 'OK',
                u'updates-archived': count,
                u'retain-removed-count': retain_removed_count}

    # Archive the data source, set the url, etc.
    def _archive_ds(self, agent, update):
        # If the ptdsx.exe doens't exist, hold off until it's there.
        if not self._have_pcmd(agent):
            return None

        # Cache these as they may no longer be available if _build_tds
        # fails.
        repository_url = update.datasource.repository_url
        revision = update.revision

        filename = self._build_tds(agent, update)
        if not filename:
            # Generates an event on error.
            logger.error('Failed to retrieve tdsx: %s %s', repository_url,
                            revision)
            return
        update.url = agent.path.basename(filename)
        logger.debug("datasource load: update.url: %s", filename)

        # retrieval is a long process, so commit after each.
        meta.Session.commit()

    def _have_pcmd(self, agent):
        """Make sure the ptdsx.exe executable is on the agent before
           we go too far along.
       """
        required_exe = self.PCMD + '.exe'
        body = agent.filemanager.listdir(agent.install_dir)
        if not required_exe in body['files']:
            logger.info("%s: Missing %s/%s.  Skipping datasource "
                          "archiving for now.", self.NAME, agent.install_dir,
                                                required_exe)
            return False
        return True

    # returns the filename *on the agent* or None on error.
    def _build_tds(self, agent, update):
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-branches
        try:
            # fixme: Specify a minimum disk space required other than 0?
            dcheck = DiskCheck(self.server, agent, self.server.DATASOURCES_DIR,
                               FileManager.FILE_TYPE_DATASOURCE, 0)
        except DiskException, ex:
            self._eventgen(update, "build_tds disk check: " + str(ex))
            return None

        tmpdir = dcheck.primary_dir
        dst = self._tabcmd_get(agent, update, tmpdir)
        if dst is None:
            # _tabcmd_get generates an event on failure.
            return None

        try:
            file_type = self.get_archive_file_type(agent, dst)
        except IOError as ex:
            self._eventgen(update, error=str(ex))
            return None

        if file_type == 'zip':
            dst_tds = self._extract_tds_from_tdsx(agent, update, dst)
            if not dst_tds:
                # _extract_tds_from_tdsx generates an event on failure.
                return None
            dst_tdsx = dst
        else:
            # It is type 'xml'.
            # Rename .tdsx to the .tds (xml) it really is.
            dst_tds = dst[0:-1] # drop the trailing 'x'
            agent.filemanager.move(dst, dst_tds)
            dst_tdsx = None
            logger.debug("datasource: renamed %s to %s", dst, dst_tds)

        # Pull the tds file contents over to the controller before sending the
        # file away (and deleting it on the primary if it will reside
        # elsewhere).
        if not self._copy_tds_to_controller(agent, update, dst_tds):
            return None

        place = self.archive_file(agent, dcheck, dst_tds)
        update.fileid_tds = place.placed_file_entry.fileid

        if dst_tdsx and self.system[SystemKeys.DATASOURCE_SAVE_TDSX]:
            place_tdsx = self.archive_file(agent, dcheck, dst_tdsx)
            update.fileid_tdsx = place_tdsx.placed_file_entry.fileid

        return dst_tds

    def _tabcmd_get(self, agent, update, tmpdir):
        """Run 'tabcmd get' on the agent to retrieve the tdsx file
           then return its path or None in the case of an error.
        """
        try:
            ds_entry = meta.Session.query(DataSourceEntry).\
                filter(DataSourceEntry.dsid == update.dsid).\
                one()
        except NoResultFound:
            logger.error("Missing datasource id: %d", update.dsid)
            return None

        url = '/datasources/%s.tdsx' % update.datasource.repository_url
        dst = agent.path.join(tmpdir,
                              self.clean_filename(ds_entry, update.revision) + \
                              '.tdsx')

        body = self.tabcmd_run(agent, url, dst, ds_entry.site_id)

        if failed(body):
            self._eventgen(update, data=body)
            if 'stderr' in body:
                if 'Not authorized' in body['stderr']:
                    self.system[SystemKeys.DATASOURCE_RETAIN_COUNT] = 0
                    self._eventgen(update, data=body, key=EventControl.\
                                   TABLEAU_ADMIN_CREDENTIALS_FAILED_DATASOURCES)
                    raise ArchiveException(ArchiveError.BAD_CREDENTIALS)
                elif '404' in body['stderr'] and "Not Found" in body['stderr']:
                    # The update was deleted before we
                    # got to it.  Subsequent attempts will also fail,
                    # so delete the update row to stop
                    # attempting to retrieve it again.
                    # Note: Don't remove the update row until after
                    # _eventgen uses it.
                    self._remove_dsu(update)
            return None
        return dst

    def _remove_dsu(self, update):
        """Remove an update from the datasource_updates table.
           We do this if a datasource update entry was listed a new datasource
           but then was deleted before we ran 'tabcmd'.
        """
        session = meta.Session()
        try:
            session.query(DataSourceUpdateEntry).\
                filter(DataSourceUpdateEntry.dsuid == update.dsuid).\
                delete()
        except NoResultFound:
            logger.error("_remove_dsu: datasource already deleted: %d",
                           update.dsuid)
            return
        session.commit()

    def _extract_tds_from_tdsx(self, agent, update, dst_tdsx):
        """
            A tdsx file is just a zipped tds + maybe tde files.
            Extract the tds and return the path.
        """
        # Make sure the *.tds file doesn't exist (it shouldn't but
        # we want to be sure).
        dst_tds = dst_tdsx[0:-1] # drop the trailing 'x' from the file ext
        try:
            agent.filemanager.delete(dst_tds)
        except IOError as ex:
            logger.debug("extract_tds_from_tdsx: Expected error deleting "
                           "datasource dst_tds '%s': %s",
                            dst_tds, str(ex))

        cmd = self.PCMD + ' ' + '"' + dst_tdsx + '"'
        body = self.server.cli_cmd(cmd, agent, timeout=60*30)

        if not self.system[SystemKeys.DATASOURCE_SAVE_TDSX]:
            # Delete the 'tdsx' since we don't archive it.
            try:
                agent.filemanager.delete(dst_tdsx)
            except IOError as ex:
                logger.debug("Error deleting datasource dst_tdsx '%s': %s",
                                dst_tdsx, str(ex))
        if failed(body):
            self._eventgen(update, data=body)
            return None
        return dst_tds

    def _copy_tds_to_controller(self, agent, update, dst_tds):
        """Copy the tds file from the Tableau server to the controller
           and save in the paldb.
           Returns:
                Failure: None
                Success: True
        """
        logger.debug('Retrieving datasource tds: %s', dst_tds)
        try:
            contents = agent.filemanager.get(dst_tds)
        except IOError as ex:
            logger.debug("Error getting datasource '%s': %s", dst_tds,
                                                                str(ex))
            return None

        update.tds = contents
        return True

    # Generate an event in case of a failure.
    def _eventgen(self, update, error=None, data=None,
                  key=EventControl.DATASOURCE_ARCHIVE_FAILED):
        if data is None:
            data = {}
        data = dict(update.datasource.todict().items() + \
                    update.todict().items() + \
                    data.items())

        self.sendevent(key, update.system_user_id, error, data)
