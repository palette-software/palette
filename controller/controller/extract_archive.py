import logging
import time

from sqlalchemy import Column, BigInteger, Integer, DateTime
from sqlalchemy import func
from sqlalchemy.schema import ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.exc import NoResultFound

import akiri.framework.sqlalchemy as meta

from archive_mixin import ArchiveUpdateMixin
from mixin import BaseMixin, BaseDictMixin
from manager import synchronized, Manager
from util import failed
from .system import SystemKeys
from datasources import DataSourceEntry
from workbooks import WorkbookEntry

from diskcheck import DiskCheck, DiskException
from event_control import EventControl
from files import FileManager

logger = logging.getLogger()

class WorkbookExtractEntry(meta.Base, BaseMixin, BaseDictMixin):
    __tablename__ = "workbook_extracts"

    sid = Column(BigInteger, unique=True, nullable=False,
                        autoincrement=True, primary_key=True)

    extractid = Column(BigInteger,
                        ForeignKey("extracts.extractid", ondelete='CASCADE'))

    parentid = Column(BigInteger,
                        ForeignKey("workbooks.workbookid", ondelete='CASCADE'))
    fileid = Column(Integer,
                         ForeignKey("files.fileid", ondelete='CASCADE'))


    creation_time = Column(DateTime, server_default=func.now())

    modification_time = Column(DateTime, server_default=func.now(), \
                                       onupdate=func.current_timestamp())

    parent = relationship('WorkbookEntry',
                           backref=backref('refresh',
                           order_by='WorkbookExtractEntry.sid'))

    @classmethod
    def add(cls, wb_entry, extract_entry):
        session = meta.Session()
        entry = WorkbookExtractEntry(parentid=wb_entry.workbookid,
                                     extractid=extract_entry.extractid)
        session.add(entry)
        session.commit()

class DataSourceExtractEntry(meta.Base, BaseMixin, BaseDictMixin):
    __tablename__ = "datasource_extracts"

    sid = Column(BigInteger, unique=True, nullable=False,
                        autoincrement=True, primary_key=True)

    extractid = Column(BigInteger,
                        ForeignKey("extracts.extractid", ondelete='CASCADE'))

    parentid = Column(BigInteger,
                        ForeignKey("datasources.dsid", ondelete='CASCADE'))

    fileid = Column(Integer,
                           ForeignKey("files.fileid", ondelete='CASCADE'))


    creation_time = Column(DateTime, server_default=func.now())

    modification_time = Column(DateTime, server_default=func.now(), \
                                       onupdate=func.current_timestamp())

    parent = relationship('DataSourceEntry',
                           backref=backref('refresh',
                           order_by='DataSourceExtractEntry.sid'))

    @classmethod
    def add(cls, ds_entry, extract_entry):
        session = meta.Session()
        entry = DataSourceExtractEntry(parentid=ds_entry.dsid,
                                       extractid=extract_entry.extractid)
        session.add(entry)
        session.commit()


class ExtractRefreshManager(Manager, ArchiveUpdateMixin):
    NAME = 'archive extract refresh'

    def add(self, item_entry, extract_entry):
        """Add a workbook or datasource entry row.
            Called with either a WorkbookEntry or DataSourceEntry row.
        """

        wb_retain_count = \
                    self.system[SystemKeys.EXTRACT_REFRESH_WB_RETAIN_COUNT]
        # future: Use separate wb and ds retain counts when UI is updated.
        ds_retain_count = wb_retain_count

        if isinstance(item_entry, WorkbookEntry):
            if wb_retain_count:
                WorkbookExtractEntry.add(item_entry, extract_entry)
        elif isinstance(item_entry, DataSourceEntry):
            if ds_retain_count:
                DataSourceExtractEntry.add(item_entry, extract_entry)
        else:
            logger.error("ExtractRefreshManager Add: Unexpected subtitle: %s",
                          extract_entry.subtitle)

    @synchronized('refresh')
    def refresh(self, agent, check_odbc_state=True):
        """Archive extract refreshes."""

        wb_retain_count = \
                    self.system[SystemKeys.EXTRACT_REFRESH_WB_RETAIN_COUNT]
        # future: Use separate wb and ds retain counts when UI is updated.
#        ds_retain_count = wb_retain_count

        if not wb_retain_count:
            logger.debug("Extract refresh archiving is not enabled.")
            return {u'disabled':
                    'Extract refresh archiving is not enabled.  Not done.'}

        # FIXME
        if check_odbc_state and not self.server.odbc_ok():
            return {u'error':
                     "Cannot run extract refresh archive while in state: %s" % \
                     self.server.state_manager.get_state()}

        self._prune_all_missed_extracts()
        return self._archive_all(agent)

    def _archive_all(self, agent):
        """Archive all extracts: Workbooks and Data Sources."""
        workbook_count = self._archive(agent, WorkbookExtractEntry)
        datasource_count = self._archive(agent, DataSourceExtractEntry)

        return {u'status': 'OK',
                u'workbook-extracts-archived': workbook_count,
                u'datasource-extracts-archive': datasource_count}

    def _archive(self, agent, obj_class):
        """Archive extracts for the object type."""

        session = meta.Session()

        updates = session.query(obj_class).\
            filter(obj_class.fileid == None).\
                       all()

        count = 0
        for update in updates:
            name = update.parent.name    # cache in case it fails and is removed
            filename = self._build_extract(agent, update)
            if not filename:
                logger.error(
                    "Failed to retrieve extract refresh: from %s: %d - %s",
                        update.__tablename__,
                        update.parentid,
                        name)
                continue

            # retrieval is a long process, so commit after each.
            meta.Session.commit()
            count += 1

        if count:
            self._retain_some()

        return count

    def _build_extract(self, agent, update):
        """Retrieve the extract refresh.
           Returns:
                Success: The filename *on the agent*
                Failure: None
        """
        date_str = time.strftime(self.server.FILENAME_FMT)

        if isinstance(update, WorkbookExtractEntry):
            archive_dir = self.server.WORKBOOKS_REFRESH_DIR
            archive_type = FileManager.FILE_TYPE_WORKBOOK
            url = '/workbooks/%s.twbx' % update.parent.repository_url
            dst = agent.path.join(self.clean_filename(update.parent,
                             date_str=date_str) + '.twbx')

        elif isinstance(update, DataSourceExtractEntry):
            archive_dir = self.server.DATASOURCES_REFRESH_DIR
            archive_type = FileManager.FILE_TYPE_DATASOURCE
            url = '/datasources/%s.tdsx' % update.parent.repository_url
            dst = agent.path.join(self.clean_filename(update.parent,
                             date_str=date_str) + '.tdsx')
        else:
            raise RuntimeError("_build_extract: bad type")

        site_id = update.parent.site_id

        try:
            # fixme: Specify a minimum disk space required other than 0?
            dcheck = DiskCheck(self.server, agent, archive_dir,
                               archive_type, 0)
        except DiskException, ex:
            self._eventgen(update, "refresh archive disk check: " + str(ex))
            return None

        dst = agent.path.join(dcheck.primary_dir, dst)

        body = self.tabcmd_run(agent, url, dst, site_id)

        if failed(body):
            self._eventgen(update, data=body)

            if 'stderr' in body and '404' in body['stderr'] and \
                                                "Not Found" in body['stderr']:

                # The extract refresh was deleted before we
                # got to it.  Subsequent attempts will also fail,
                # so delete the row to stop attempting to retrieve it again.
                # Note: We didn't remove the row until after
                # _eventgen used it.
                self._remove_refresh_entry(update)
            return None

        if dst is None:
            # _tabcmd_get generates an event on failure
            return None

        place = self.archive_file(agent, dcheck, dst)
        update.fileid = place.placed_file_entry.fileid

        return dst

    def _remove_refresh_entry(self, update):
        """Remove a refresh extract entry from the workbook_extracts or
           datasource_extracts table."""

        session = meta.Session()
        try:
            session.query(update.__class__).\
                filter(update.__class__.sid == update.sid).\
                delete()
        except NoResultFound:
            logger.error(
                "_remove_refresh_entry: %s extract already deleted: %d",
                           update.__tablename__,
                           update.sid)
            return

        session.commit()

        return

    def _prune_all_missed_extracts(self):
        """We might have missed some extracts, for example if the
           tabcmd failed, things took too long, etc.
           If so, remove the missed extracts from our tables.
           If multiple rows with the same parentid and empty fileid
           exist (unarchived), keep only the most recent row.
        """

        total_rowcount = 0

        for obj_class in [WorkbookExtractEntry, DataSourceExtractEntry]:
            stmt = ("delete from %s where " + \
                    "(parentid, sid) not in " + \
                    "(select parentid, max(sid) " + \
                    "from %s where fileid is null " + \
                    "group by parentid) " + \
                    "and fileid is null;") % (obj_class.__tablename__,
                                                  obj_class.__tablename__)

            connection = meta.get_connection()
            result = connection.execute(stmt)
            connection.close()

            if result.rowcount:
                logger.debug("refresh _prune_missed_extracts for %s pruned %d",
                           obj_class.__tablename__, result.rowcount)

                total_rowcount += result.rowcount

        return total_rowcount

    def _retain_some(self):
        """Retain only the configured number of extract refresh archives
           for each workbook or datasource.
            Returns:
                    The number of archive versions removed.
        """

        wb_retain_count = \
                        self.system[SystemKeys.EXTRACT_REFRESH_WB_RETAIN_COUNT]
        if not wb_retain_count:
            return 0

        wb_removed_count = self._retain_some_obj(wb_retain_count,
                                             WorkbookExtractEntry)
        ds_removed_count = self._retain_some_obj(wb_retain_count,
                                             DataSourceExtractEntry)

        return wb_removed_count + ds_removed_count

    def _retain_some_obj(self, retain_count, obj_class):
        """Do the removal of excess WorkbookExtractEntry or
           DataSourceExtractEntry rows.

           Called with:
                - How many to retain
                - The object class (WorkbookExtractEntry or
                                    DataSourceExtractEntry
        """

        session = meta.Session()
        # List of parentids that have excess archived versions:
        #   [(parentid, total-count), ...]
        # Note we select only successfully archived extracts when
        # fileid != None.  We don't want want to count unsuccessfully
        # archived extracts in the count of how many we have.
        results = session.query(obj_class.parentid, func.count()).\
                  filter(obj_class.fileid != None).\
                  group_by(obj_class.parentid).\
                  having(func.count() > retain_count).\
                  all()

        logger.debug("refresh _retain_some_obj %s len: %d, results: %s",
                     obj_class.__tablename__, len(results), str(results))

        removed_count = 0
        for result in results:
            # Get the list of rows to delete
            rows = session.query(obj_class).\
                    filter(obj_class.parentid == result[0]).\
                    filter(obj_class.fileid != None).\
                    order_by(obj_class.sid.asc()).\
                    limit(result[1] - retain_count).\
                    all()

            for row in rows:
                # We have to remove the extract row first
                # due to the foreign key constraint in the files table
                # pointing to it.
                session.query(obj_class).\
                            filter(obj_class.sid == row.sid).\
                            delete()
                session.commit()

                self.server.files.remove_file_by_id(row.fileid)

                # Fixme: We could increment only if it successfully deleted.
                removed_count += 1

        return removed_count

    # Generate an event in case of a failure.
    def _eventgen(self, update, error=None, data=None):
        if data is None:
            data = {}

        if isinstance(update, WorkbookExtractEntry):
            key = EventControl.WORKBOOK_REFRESH_ARCHIVE_FAILED
        elif isinstance(update, DataSourceExtractEntry):
            key = EventControl.DATASOURCE_REFRESH_ARCHIVE_FAILED

        data = dict(update.parent.todict().items() + \
                    update.todict().items() + \
                    data.items())
        if 'embedded' in data:
            del data['embedded']

        self.sendevent(key, update.parent.system_user_id, error, data)
