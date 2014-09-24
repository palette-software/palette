import os

from sqlalchemy import Column, BigInteger, Integer, Boolean, String, DateTime
from sqlalchemy import UniqueConstraint
from sqlalchemy.schema import ForeignKey
from sqlalchemy.orm import relationship, backref

# pylint: disable=import-error,no-name-in-module
from akiri.framework.ext.sqlalchemy import meta
# pylint: enable=import-error,no-name-in-module

from mixin import BaseMixin, BaseDictMixin
from cache import TableauCacheManager
from util import failed, success
from odbc import ODBC

from diskcheck import DiskCheck, DiskException
from event_control import EventControl
from place_file import PlaceFile
from files import FileManager

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

    __table_args__ = (UniqueConstraint('envid', 'id'),
                      UniqueConstraint('envid', 'name'))

    def fileext(self):
        if self.data_engine_extracts:
            return 'twbx'
        return 'twb'

    @classmethod
    def get(cls, envid, name, **kwargs):
        keys = {'envid':envid, 'name':name}
        return cls.get_unique_by_keys(keys, **kwargs)

    @classmethod
    def get_all_by_envid(cls, envid):
        return cls.get_all_by_keys({'envid':envid}, order_by='name')

    @classmethod
    def get_all_by_system_user(cls, envid, system_user_id):
        filters = {'envid':envid, 'system_user_id':system_user_id}
        return cls.get_all_by_keys(filters, order_by='name')


class WorkbookUpdateEntry(meta.Base, BaseMixin, BaseDictMixin):
    __tablename__ = "workbook_updates"

    wuid = Column(BigInteger, unique=True, nullable=False, \
                  autoincrement=True, primary_key=True)
    workbookid = Column(BigInteger, ForeignKey("workbooks.workbookid"))
    revision = Column(String, nullable=False)
    fileid = Column(Integer, ForeignKey("files.fileid"))
    timestamp = Column(DateTime, nullable=False)
    system_user_id = Column(Integer)
    url = Column(String)  # FIXME: make this unique.
    note = Column(String)

    # NOTE: system_user_id is not a foreign key to avoid load dependencies.

    workbook = relationship('WorkbookEntry', \
        backref=backref('updates',
                        order_by='desc(WorkbookUpdateEntry.revision)')
    )

    __table_args__ = (UniqueConstraint('workbookid', 'revision'),)

    # ideally: site-project-name-rev.twb
    def basename(self):
        # pylint: disable=no-member
        return self.workbook.repository_url + '-rev' + self.revision

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


class WorkbookManager(TableauCacheManager):

    def __init__(self, server):
        super(WorkbookManager, self).__init__(server)
        path = server.config.get('palette', 'workbook_archive_dir')
        self.path = os.path.abspath(path)

    # really sync *and* load
    def load(self, agent):
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        if not self.cred_check():
            return {u'error': 'Can not load workbooks: missing credentials.'}

        if not self.lock(blocking=False):
            return {u'error': 'Can not load workbooks: busy.'}

        envid = self.server.environment.envid
        users = self.load_users(agent)

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

        last_created_at = self.last_created_at(envid)
        if last_created_at:
            # NOTE: the precision of the updated_at timestamp on windows
            # is greater than that on linux so this where clause often
            # returns at least one entry (if the table is non-empty)
            stmt += " WHERE created_at > '" + last_created_at + "'"

        data = agent.odbc.execute(stmt)

        updates = []
        schema = self.schema(data)

        if 'error' in data or '' not in data:
            self.log.debug("workbooks load: bad data: %s", str(data))
            self.unlock()
            return data

        self.log.debug(data)

        for odbcdata in ODBC.load(data):
            name = odbcdata.data['name']
            revision = odbcdata.data['revision']

            wbe = WorkbookEntry.get(envid, name, default=None)
            if wbe is None:
                wbe = WorkbookEntry(envid=envid, name=name)
                session.add(wbe)

            # NOTE: id is updated with each revision.
            odbcdata.copyto(wbe, excludes=['revision'])

            system_user_id = users.get(wbe.site_id, wbe.owner_id)
            wbe.system_user_id = system_user_id

            # must commit here so that update foreign keys work.
            session.commit()

            wbu = WorkbookUpdateEntry.get(wbe.workbookid,
                                          revision,
                                          default=None)
            if not wbu:
                # A new row is created each time in the Tableau database,
                # so the created_at time is actually the publish time.
                wbu = WorkbookUpdateEntry(workbookid=wbe.workbookid,
                                          revision=revision,
                                          system_user_id=system_user_id,
                                          timestamp=wbe.created_at,
                                          url='')
                session.add(wbu)
                updates.append(wbu)

            self.log.debug("workbook update '%s', revision %s", name, revision)

        session.commit()

        # Second pass - build the archive files.
        for update in updates:
            session.refresh(update)
            filename = self.retrieve_workbook(update, agent)
            if not filename:
                self.log.error('Failed to retrieve workbook: %s %s',
                               update.workbook.repository_url, revision)
                continue
            update.url = filename
            self.log.debug("workbooks load: update.url: %s", filename)
            # retrieval is a long process, so commit after each.
            session.commit()

        self.unlock()
        return {u'status': 'OK',
                u'schema': schema,
                u'updates':str(len(updates))}

    # returns the filename *on the agent* or None on error.
    def build_workbook(self, update, agent):
        # pylint: disable=too-many-statements
        try:
            # fixme: Specify a minimum disk space required other than 0?
            dcheck = DiskCheck(self.server, agent, self.server.WORKBOOKS_DIR,
                               FileManager.FILE_TYPE_WORKBOOK, 0)
        except DiskException, ex:
            self._eventgen(update, "build_workbook disk check : " + str(ex))
            return None

        tmpdir = dcheck.primary_dir
        ext = update.workbook.fileext()
        url = '/workbooks/' + update.workbook.repository_url + '.' + ext
        dst = agent.path.join(tmpdir, update.basename() + '.' + ext)
        cmd = 'get %s -f "%s"' % (url, dst)

        self.log.debug('building workbook archive: ' + dst)

        body = self.server.tabcmd(cmd, agent)
        if failed(body):
            self._eventgen(update, data=body)
            return None
        if ext == 'twbx':
            dst = self._extract_twb_from_twbx(agent, update, tmpdir, dst)
            if not dst:
                # _extract_twb_from_twbx generates an event on failure.
                return None
        # move twbx/twb to resting location.
        file_size_body = agent.filemanager.filesize(dst)
        if not success(file_size_body):
            self.log.error(
                "build_workbook: Failed to get size of workbook file %s: %s",
                dst, file_size_body['error'])
            file_size = 0
        else:
            file_size = file_size_body['size']

        auto = True
        place = PlaceFile(self.server, agent, dcheck, dst, file_size, auto,
                          enable_delete=False)
        self.log.debug("build_workbook: %s", place.info)
        # Remember the fileid
        update.fileid = place.placed_file_entry.fileid
        return dst

    # returns the filename - in self.path - or None on error.
    def retrieve_workbook(self, update, agent):
        path = self.build_workbook(update, agent)
        if not path:
            # build_workbook prints errors and calls _eventgen().
            return None
        self.log.debug('Retrieving workbook: %s', path)
        try:
            body = agent.filemanager.save(path, target=self.path)
        except IOError as ex:
            self.log.debug("Error saving workbook '%s': %s", path, str(ex))
            return None

        if failed(body):
            self._eventgen(self, update, data=body)
            return None
        else:
            self.log.debug('Retrieved workbook: %s', path)
        agent.filemanager.delete(path)
        return agent.path.basename(path)

    # This is the time the last revision was created.
    # returns a UTC string or None
    def last_created_at(self, envid):
        value = WorkbookEntry.max('created_at', filters={'envid':envid})
        if value is None:
            return None
        return str(value)

    def cred_check(self):
        """Returns None if there are credentials and Non-None/False
           if there are credentials."""

        cred = self.server.cred.get('primary', default=None)
        if not cred:
            cred = self.server.cred.get('secondary', default=None)

        return cred

    # A twbx file is just a zipped twb + associated tde files.
    # Extract the twb and return the path.
    def _extract_twb_from_twbx(self, agent, update, tmpdir, dst):
        cmd = 'ptwbx ' + '"' + dst + '"'
        body = self.server.cli_cmd(cmd, agent)
        if failed(body):
            self._eventgen(update, data=body)
            agent.filemanager.delete(dst)
            return None
        dst = agent.path.join(tmpdir, update.basename() + '.twb')
        return dst

    def _eventgen(self, update, error=None, data=None):
        key = EventControl.WORKBOOK_ARCHIVE_FAILED
        if data is None:
            data = {}
        data = dict(update.workbook.todict().items() + \
                    update.todict().items() + \
                    data.items())
        if 'embedded' in data:
            del data['embedded']
        if error:
            self.log.error(error)
            data['error'] = error
        return self.server.event_control.gen(key, data)
