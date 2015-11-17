import logging
import os

from sqlalchemy import Column, BigInteger, Integer, Boolean, String, DateTime
from sqlalchemy import UniqueConstraint, Text
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy.schema import ForeignKey
from sqlalchemy.orm import relationship, backref, deferred
from sqlalchemy.orm.exc import NoResultFound

import akiri.framework.sqlalchemy as meta

from archive_mixin import ArchiveUpdateMixin, ArchiveException, ArchiveError
from mixin import BaseMixin, BaseDictMixin
from cache import TableauCacheManager #FIXME
from manager import synchronized
from util import failed
from odbc import ODBC
from .system import SystemKeys

from diskcheck import DiskCheck, DiskException
from event_control import EventControl
from files import FileManager

from sites import Site
from projects import Project

logger = logging.getLogger()


# NOTE: system_user_id is maintained in two places.  This is not ideal from
# a db design perspective but makes the find-by-current-owner code clearer.
class WorkbookEntry(meta.Base, BaseMixin, BaseDictMixin):
    __tablename__ = "workbooks"

    workbookid = Column(BigInteger, unique=True, nullable=False,
                        autoincrement=True, primary_key=True)
    envid = Column(BigInteger, ForeignKey("environment.envid"), nullable=False)
    system_user_id = Column(Integer)
    id = Column(BigInteger, nullable=False)
    name = Column(String)
    repository_url = Column(String)
    description = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    owner_id = Column(Integer)
    project_id = Column(Integer)
    view_count = Column(Integer)
    size = Column(BigInteger)
    embedded = Column(String)
    thumb_user = Column(String)
    refreshable_extracts = Column(Boolean)
    extracts_refreshed_at = Column(DateTime)
    lock_version = Column(Integer)
    state = Column(String)
    version = Column(String)
    checksum = Column(String)
    display_tabs = Column(Boolean)
    data_engine_extracts = Column(Boolean)
    incrementable_extracts = Column(Boolean)
    site_id = Column(Integer)
    repository_data_id = Column(BigInteger)
    repository_extract_data_id = Column(BigInteger)
    first_published_at = Column(DateTime)
    primary_content_url = Column(String)
    share_description = Column(String)
    show_toolbar = Column(Boolean)
    extracts_incremented_at = Column(DateTime)
    default_view_index = Column(Integer)
    luid = Column(String)
    assert_key_id = Column(Integer)
    document_version = Column(String)

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
    def get_by_id(cls, envid, workbook_id):
        return cls.get_unique_by_keys({'envid': envid, 'id': workbook_id})

    @classmethod
    def get_newest_by_id(cls, envid, workbook_id):
        rows = cls.get_all_by_keys({'envid': envid, 'id': workbook_id},
                                order_by=[WorkbookEntry.updated_at.desc()],
                                limit=1)
        if not rows:
            return None
        return rows[0]

    @classmethod
    def get_by_url(cls, envid, url, site_id, **kwargs):
        # technically the Tableau database does not guarantee uniqueness.
        keys = {'envid':envid, 'repository_url': url, 'site_id': site_id}
        return cls.get_unique_by_keys(keys, **kwargs)

    @classmethod
    def get_all_by_envid(cls, envid):
        return cls.get_all_by_keys({'envid':envid}, order_by='name')

    @classmethod
    def get_all_by_system_user(cls, envid, system_user_id):
        filters = {'envid':envid, 'system_user_id':system_user_id}
        return cls.get_all_by_keys(filters, order_by='name')

    @classmethod
    def get_last_updated_at(cls, envid):
        """Returns the most recent 'updated_at' value for the table,
           if it exists, or None if the table is empty.
         """
        value = cls.max('updated_at', filters={'envid':envid})
        if value is None:
            return None
        return str(value)

class WorkbookUpdateEntry(meta.Base, BaseMixin, BaseDictMixin):
    __tablename__ = "workbook_updates"

    wuid = Column(BigInteger, unique=True, nullable=False, \
                  autoincrement=True, primary_key=True)
    workbookid = Column(BigInteger,
                        ForeignKey("workbooks.workbookid", ondelete='CASCADE'))
    revision = Column(String, nullable=False)
    fileid = Column(Integer, ForeignKey("files.fileid", ondelete='CASCADE'))
    fileid_twbx = Column(Integer,
                         ForeignKey("files.fileid", ondelete='CASCADE'))
    timestamp = Column(DateTime, nullable=False)
    system_user_id = Column(Integer)
    url = Column(String)  # FIXME: make this unique.
    note = Column(String)
    twb = deferred(Column(Text))    # the contents of the .twb file

    # NOTE: system_user_id is not a foreign key to avoid load dependencies.

    workbook = relationship('WorkbookEntry', \
        backref=backref('updates',
                        order_by='desc(WorkbookUpdateEntry.revision)')
    )

    __table_args__ = (UniqueConstraint('workbookid', 'revision'),)

    @classmethod
    def get(cls, wbid, revision, **kwargs):
        return cls.get_unique_by_keys({'workbookid': wbid,
                                       'revision': revision},
                                      **kwargs)

    @classmethod
    def get_by_id(cls, wuid, **kwargs):
        return cls.get_unique_by_keys({'wuid': wuid}, **kwargs)

    @classmethod
    def get_by_url(cls, url, **kwargs):
        return cls.get_unique_by_keys({'url': url}, **kwargs)


class WorkbookManager(TableauCacheManager, ArchiveUpdateMixin):
    NAME = 'workbook'

    def __init__(self, server):
        super(WorkbookManager, self).__init__(server)
        self.sample_project_id = None
        sample_project_entry = Project.get_by_name(
                                                self.server.environment.envid,
                                                'Tableau Samples')
        if sample_project_entry:
            self.sample_project_id = sample_project_entry.id

    def move_twb_to_db(self):
        """Copy the twb file contents on the controller to the database
           and remove the twb files.
        """

        path = self.server.config.get('palette', 'workbook_archive_dir')
        controller_path = os.path.abspath(path)

        session = meta.Session()
        rows = session.query(WorkbookUpdateEntry).\
                            filter(WorkbookUpdateEntry.url != '').\
                            filter(WorkbookUpdateEntry.url != None).\
                            filter(WorkbookUpdateEntry.twb == None).\
                            all()

        for row in rows:
            twb_path = os.path.join(controller_path, row.url)
            try:
                with open(twb_path, "r") as fd_twb:
                    contents = fd_twb.read()
            except IOError as err:
                logger.error("move_twb_to_db open failed: %s", str(err))
                continue

            row.twb = contents
            session.commit()

            twb_path = os.path.join(controller_path, row.url)
            os.unlink(twb_path)

    # really sync *and* load
    @synchronized('workbooks')
    def load(self, agent):
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements

        envid = self.server.environment.envid
        if not self.sample_project_id:
            sample_project_entry = Project.get_by_name(envid,
                                                       'Tableau Samples')
            if sample_project_entry:
                self.sample_project_id = sample_project_entry.id

        stmt = \
            'SELECT id, name, repository_url, description,' +\
            ' created_at, updated_at, owner_id, project_id,' +\
            ' view_count, size, embedded, thumb_user,' +\
            ' refreshable_extracts, extracts_refreshed_at, lock_version,' +\
            ' state, version, checksum, display_tabs, data_engine_extracts,' +\
            ' incrementable_extracts, site_id, revision,' +\
            ' repository_data_id, repository_extract_data_id,' +\
            ' first_published_at, primary_content_url, share_description,' +\
            ' show_toolbar, extracts_incremented_at, default_view_index,' +\
            ' luid, asset_key_id, document_version ' +\
            'FROM workbooks'

        session = meta.Session()

        last_updated_at = WorkbookEntry.get_last_updated_at(envid)
        if last_updated_at:
            stmt += " WHERE updated_at > '" + last_updated_at + "'"

        data = agent.odbc.execute(stmt)

        updates = []

        if 'error' in data or '' not in data:
            logger.debug("workbooks load: bad data: %s", str(data))
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

            if project_id == self.sample_project_id:
                logger.debug(
                        "workbooks load: Ignoring Tableau Sample wb: %s, %s",
                        name, revision)
                continue

            wbe = WorkbookEntry.get(envid, site_id, project_id, luid,
                                                            default=None)
            if wbe is None:
                wbe = WorkbookEntry(envid=envid, site_id=site_id,
                                    project_id=project_id, luid=luid)
                session.add(wbe)

            # NOTE: id is updated with each revision.
            odbcdata.copyto(wbe, excludes=['revision'])

            if not users:
                users = self.load_users(agent)

            system_user_id = users.get(wbe.site_id, wbe.owner_id)
            wbe.system_user_id = system_user_id

            # must commit here so that update foreign keys work.
            session.commit()

            wbu = WorkbookUpdateEntry.get(wbe.workbookid,
                                          revision,
                                          default=None)
            if not wbu:
                # The updated_at time is the publish time.
                wbu = WorkbookUpdateEntry(workbookid=wbe.workbookid,
                                          revision=revision,
                                          system_user_id=system_user_id,
                                          timestamp=wbe.updated_at,
                                          url='')
                session.add(wbu)
                updates.append(wbu)

            logger.debug("workbook update '%s', revision %s", name, revision)

        session.commit()

        prune_count = self._prune_missed_revisions()

        if not self.system[SystemKeys.WORKBOOK_ARCHIVE_ENABLED]:
            result = {u'disabled':
                      'Workbook Archives are not enabled. Will not archive.'}
        elif not self.cred_check():
            result = {u'error': 'Can not load workbooks: missing credentials.'}
        else:
            # Second pass - build the archive files.
            result = self._archive_updates(agent, updates)

        result[u'schema'] = self.schema(data)
        result[u'updates-new'] = len(updates)
        result[u'updates-missed'] = prune_count

        return result

    def _prune_missed_revisions(self):
        """Remove rows from workbook_updates that we didn't manage to
           archive.  It may be due to bad credentials, failed tabcmd, etc.
           Returns:
                count of updates pruned.
        """

        stmt = "delete from workbook_updates where " + \
                "(workbookid, timestamp) not in "+ \
                    "(select workbookid, max(timestamp) "+ \
                    "from workbook_updates where url='' " + \
                    "group by workbookid) " + \
                    "and url='';"

        connection = meta.get_connection()
        result = connection.execute(stmt)
        connection.close()

        if result.rowcount:
            logger.debug("workbooks _prune_missed_revisions pruned %d",
                           result.rowcount)

        return result.rowcount

    def _retain_some(self):
        """Retain only the configured number of workbook versions.
            Returns:
                    The number of archive versions removed.
        """

        retain_count = self.system[SystemKeys.WORKBOOK_RETAIN_COUNT]
        if not retain_count or retain_count == -1:
            return 0

        removed_count = 0

        session = meta.Session()
        # List of workbooks that have excess archived versions:
        #   [(workbookid, total-count), ...]
        # Note we select only successfully archived workbook versions
        # (url != '').  We don't want want to count unsuccessfully
        # archived versions in the count of how many we have.
        results = session.query(WorkbookUpdateEntry.workbookid, func.count()).\
                  filter(WorkbookUpdateEntry.url != '').\
                  group_by(WorkbookUpdateEntry.workbookid).\
                  having(func.count() > retain_count).\
                  all()

#        logger.debug("workbooks _retain_some len: %d, results: %s",
#                                                len(results), str(results))

        for result in results:
            # Get list of old workbook archive entries to delete
            rows = session.query(WorkbookUpdateEntry).\
                    filter(WorkbookUpdateEntry.workbookid == result[0]).\
                    filter(WorkbookUpdateEntry.url != '').\
                    order_by(WorkbookUpdateEntry.timestamp.asc()).\
                    limit(result[1] - retain_count).\
                    all()

            for row in rows:
                # We have to remove the WorkbookUpdateEntry first
                # due to the foreign key constraint in files pointing to it.
                session.query(WorkbookUpdateEntry).\
                            filter(WorkbookUpdateEntry.wuid == row.wuid).\
                            delete()
                session.commit()

                self.server.files.remove_file_by_id(row.fileid)
                if row.fileid_twbx:
                    self.server.files.remove_file_by_id(row.fileid_twbx)

                # Fixme: We could increment only if it successfully deleted.
                removed_count += 1

        return removed_count

    @synchronized('workbook.fixup')
    def fixup(self, agent):
        if not self.system[SystemKeys.WORKBOOK_ARCHIVE_ENABLED]:
            logger.debug("Workbook archives are not enabled. Fixup not done.")
            return {u'disabled':
                    'Workbook Archives are not enabled.  Fixup not done.'}

        session = meta.Session()

        # potentially serveral thousand?
        updates = session.query(WorkbookUpdateEntry).\
                  filter(or_(WorkbookUpdateEntry.url == "",
                         WorkbookUpdateEntry.url == None)).\
                         all()

        return self._archive_updates(agent, updates)

    def _archive_updates(self, agent, updates):
        """Attempt to archive workbooks from WorkbookUpdate rows."""

        session = meta.Session()

        count = 0
        data = {}
        logger.debug("Workbook archive update count: %d\n", len(updates))
        for update in updates:
            if not self.system[SystemKeys.WORKBOOK_ARCHIVE_ENABLED]:
                logger.info(
                          "Workbook Archive disabled during fixup." + \
                          "  Exiting for now.")
                break

            if not self.server.odbc_ok():
                logger.info("Workbook Archive Fixup: Archive build " + \
                          "stopping due to current state")
                break

            logger.debug("Workbook archive update refresh wid %d",
                           update.workbookid)
            session.refresh(update)
            try:
                self._archive_wb(agent, update)
            except ArchiveException as ex:
                if ex.value == ArchiveError.BAD_CREDENTIALS:
                    msg = "workbook _archive_updates: tabcmd failed due to " + \
                          "bad credentials. " + \
                          "Skipping any remaining workbook updates now."
                    logger.info(msg)
                    data[u'error'] = msg
                    break
                else:
                    raise # should never happen
            count += 1

        # Retain only configured number of versions
        if count:
            retain_removed_count = self._retain_some()
        else:
            retain_removed_count = 0

        data[u'updates-archived'] = count
        data[u'retain-removed-count'] = retain_removed_count
        return data

    def _archive_wb(self, agent, update):
        """
            Retrieve the twb/twbx file of an update and set the url.
        """
        # Cache these as they may no longer be available if _build_twb
        # fails.
        repository_url = update.workbook.repository_url
        revision = update.revision

        filename = self._build_twb(agent, update)
        if not filename:
            logger.error('Failed to retrieve twb: %s %s', repository_url,
                                                            revision)
            return
        update.url = agent.path.basename(filename)
        logger.debug("workbooks load: update.url: %s", filename)

        # retrieval is a long process, so commit after each.
        meta.Session.commit()

    def _build_twb(self, agent, update):
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-branches
        """Returns the filename *on the agent* or None on error."""

        try:
            # fixme: Specify a minimum disk space required other than 0?
            dcheck = DiskCheck(self.server, agent, self.server.WORKBOOKS_DIR,
                               FileManager.FILE_TYPE_WORKBOOK, 0)
        except DiskException, ex:
            self._eventgen(update, "build_workbook disk check : " + str(ex))
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
            dst_twb = self._extract_twb_from_twbx(agent, update, dst)
            if not dst_twb:
                # _extract_twb_from_twbx generates an event on failure.
                return None
            dst_twbx = dst
        else:
            # It is type 'xml'.
            # Rename .twbx to the .twb (xml) it really is.
            dst_twb = dst[0:-1] # drop the trailing 'x'
            agent.filemanager.move(dst, dst_twb)
            dst_twbx = None
            logger.debug("workbook: renamed %s to %s", dst, dst_twb)

        # Pull the twb file contents over to the controller before sending the
        # file away (and deleting it on the primary if it will reside
        # elsewhere).
        if not self._copy_twb_to_controller(agent, update, dst_twb):
            return None

        place = self.archive_file(agent, dcheck, dst_twb)
        update.fileid = place.placed_file_entry.fileid

        if dst_twbx and self.system[SystemKeys.ARCHIVE_SAVE_TWBX]:
            place_twbx = self.archive_file(agent, dcheck, dst_twbx)
            update.fileid_twbx = place_twbx.placed_file_entry.fileid

        return dst_twb

    def _copy_twb_to_controller(self, agent, update, dst_twb):
        """Copy the twb file from the Tableau server to the controller.
           Returns:
                Failure: None
                Success: The passed filename
        """
        logger.debug('Retrieving workbook: %s', dst_twb)
        try:
            contents = agent.filemanager.get(dst_twb)
        except IOError as ex:
            logger.debug("Error getting workbook '%s': %s", dst_twb, str(ex))
            return None

        update.twb = contents
        return True

    def _tabcmd_get(self, agent, update, tmpdir):
        """
            Run 'tabcmd get' on the agent to retrieve the twb/twbx file
            then return its path or None in the case of an error.
        """
        try:
            wb_entry = meta.Session.query(WorkbookEntry).\
                filter(WorkbookEntry.workbookid == update.workbookid).\
                one()
        except NoResultFound:
            logger.error("Missing workbook id: %d", update.workbookdid)
            return None

        url = '/workbooks/%s.twbx' % update.workbook.repository_url

        dst = agent.path.join(tmpdir,
                             self.clean_filename(wb_entry, update.revision) + \
                             '.twbx')

        body = self.tabcmd_run(agent, url, dst, wb_entry.site_id)

        if failed(body):
            self._eventgen(update, data=body)
            if 'stderr' in body:
                if 'Not authorized' in body['stderr']:
                    self.system[SystemKeys.WORKBOOK_ARCHIVE_ENABLED] = False
                    self._eventgen(update, data=body,
                            key=EventControl.\
                                    TABLEAU_ADMIN_CREDENTIALS_FAILED_WORKBOOKS)
                    raise ArchiveException(ArchiveError.BAD_CREDENTIALS)
                elif '404' in body['stderr'] and "Not Found" in body['stderr']:
                    # The update was deleted before we
                    # got to it.  Subsequent attempts will also fail,
                    # so delete the update row to stop
                    # attempting to retrieve it again.
                    # Note: We didn't remove the update row until after
                    # _eventgen used it.
                    self._remove_wbu(update)
                return None
        return dst

    def _remove_wbu(self, update):
        """Remove an update from the workbook_updates table.
           We do this if a workbook update entry listed a new workbook
           but then was deleted before we ran 'tabcmd'.
        """
        session = meta.Session()
        try:
            session.query(WorkbookUpdateEntry).\
                filter(WorkbookUpdateEntry.wuid == update.wuid).\
                delete()
        except NoResultFound:
            logger.error("_remove_wbu: workbook already deleted: %d",
                           update.wuid)
            return
        session.commit()

    def _extract_twb_from_twbx(self, agent, update, dst):
        """A twbx file is just a zipped twb + associated tde files.
           Extract the twb and return the path.
           Returns:
                Success:    The twb filename on the agent.
                Fail:       None
        """
        cmd = 'ptwbx ' + '"' + dst + '"'
        body = self.server.cli_cmd(cmd, agent, timeout=60*30)

        if not self.system[SystemKeys.ARCHIVE_SAVE_TWBX]:
            # Delete the 'twbx' since we don't archive it.
            try:
                agent.filemanager.delete(dst)
            except IOError as ex:
                logger.debug("Error deleting workbook dst '%s': %s",
                                dst, str(ex))
        if failed(body):
            self._eventgen(update, data=body)
            return None
        dst = dst[0:-1] # drop the trailing 'x' from the file extension.
        return dst

    # Generate an event in case of a failure.
    def _eventgen(self, update, error=None, data=None,
                                key=EventControl.WORKBOOK_ARCHIVE_FAILED):
        if data is None:
            data = {}

        data = dict(update.workbook.todict().items() + \
                    update.todict().items() + \
                    data.items())
        if 'embedded' in data:
            del data['embedded']

        self.sendevent(key, update.system_user_id, error, data)
