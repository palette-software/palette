import time
from sqlalchemy import Column, BigInteger, Integer, Boolean, String, DateTime
from sqlalchemy import func, UniqueConstraint
from sqlalchemy.schema import ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.exc import NoResultFound

from akiri.framework.ext.sqlalchemy import meta

from mixin import BaseDictMixin
from cache import TableauCacheManager
from util import odbc2dt

class WorkbookEntry(meta.Base, BaseDictMixin):
    __tablename__ = "workbooks"

    workbookid = Column(BigInteger, unique=True, nullable=False,
                        autoincrement=True, primary_key=True)
    envid = Column(Integer, ForeignKey("environment.envid"), nullable=False)
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

    __table_args__ = (UniqueConstraint('envid', 'id'),)

    @classmethod
    def all_by_envid(cls, envid):
        return meta.Session.query(cls).\
            filter(cls.envid == envid).all()

    @classmethod
    def get(cls, envid, wbid, **kwargs):
        if 'default' in kwargs:
            default = kwargs['default']
            have_default = True
            del kwargs['default']
        else:
            have_default = False

        if kwargs:
            raise ValueError("Invalid kwargs")

        try:
            entry = meta.Session.query(cls).\
                filter(cls.envid == envid).\
                filter(cls.id == wbid).\
                one()
        except NoResultFound, e:
            if have_default:
                return default
            raise ValueError("No such workbook: " + str(wbid))
        return entry


class WorkbookUpdateEntry(meta.Base, BaseDictMixin):
    __tablename__ = "workbook_updates"

    wuid = Column(BigInteger, unique=True, nullable=False, \
                  autoincrement=True, primary_key=True)
    workbookid = Column(BigInteger, ForeignKey("workbooks.workbookid"))
    revision = Column(String, nullable=False)
    timestamp = Column(DateTime, server_default=func.now())
    system_users_id = Column(Integer)
    url = Column(String)

    # NOTE: system_users_id is not a foreign key to avoid load dependencies.

    workbook = relationship('WorkbookEntry', \
        backref=backref('updates',
                        order_by='desc(WorkbookUpdateEntry.timestamp)')
    )

    __table_args__ = (UniqueConstraint('workbookid', 'revision'),)

    @classmethod
    def get(cls, wbid, revision, **kwargs):
        if 'default' in kwargs:
            default = kwargs['default']
            have_default = True
            del kwargs['default']
        else:
            have_default = False

        if kwargs:
            raise ValueError("Invalid kwargs")

        try:
            entry = meta.Session.query(cls).\
                filter(cls.workbookid == wbid).\
                filter(cls.revision == revision).\
                one()
        except NoResultFound, e:
            if have_default:
                return default
            raise ValueError("No such workbook update: (%d, %s)" %\
                             (wbid,revision))
        return entry


class WorkbookManager(TableauCacheManager):

    def load(self, agent):
        envid = self.server.environment.envid
        self.prune(agent)

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

        last_update = self.last_update()
        if last_update:
            # NOTE: the precision of the updated_at timestamp on windows
            # is greater than that on linux so this where clause always
            # returns at least one entry (if the table is non-empty)
            stmt += " WHERE updated_at > '" + last_update + "'"

        data = agent.odbc.execute(stmt)

        schema = self.schema(data)

        if 'error' in data or '' not in data:
            return data

        self.server.log.debug(data)

        for row in data['']:
            wbid = row[0]
            revision = row[22]
            updated_at = odbc2dt(row[5])

            wb = WorkbookEntry.get(envid, wbid, default=None)
            if wb is None:
                wb = WorkbookEntry(envid=envid, id=wbid)
                session.add(wb)

            wb.name = row[1]
            wb.repository_url = row[2]
            wb.description = row[3]
            wb.created_at = odbc2dt(row[4])
            wb.updated_at = updated_at
            wb.owner_id = row[6]
            wb.project_id = row[7]
            wb.view_count = row[8]
            wb.size = row[9]
            wb.embedded = row[10]
            wb.thumb_user = row[11]
            wb.refreshable_extracts = row[12]
            wb.extracts_refreshed_at = odbc2dt(row[13])
            wb.lock_version = row[14]
            wb.state = row[15]
            wb.version = row[16]
            wb.checksum = row[17]
            wb.display_tabs = row[18]
            wb.data_engine_extracts = row[19]
            wb.incrementable_extracts = row[20]
            wb.site_id = row[21]
            wb.repository_data_id = row[23]
            wb.repository_extract_data_id = row[24]
            wb.first_published_at = odbc2dt(row[25])
            wb.primary_content_url = row[26]
            wb.share_description = row[27]
            wb.show_toolbar = row[28]
            wb.extracts_incremented_at = odbc2dt(row[29])
            wb.default_view_index = row[30]
            wb.luid = row[31]
            wb.asset_key_id = row[32]
            wb.document_version = row[33]

            # Must commit after each row so that wookbookid(wb.id) is set.
            # session.commit()

            wbu = WorkbookUpdateEntry.get(wbid, revision, default=None)
            if not wbu:
                system_users_id = users.get(wb.site_id, wb.owner_id)
                timestamp = updated_at and updated_at or wb.created_at
                wbu = WorkbookUpdateEntry(workbookid=wb.workbookid,
                                          revision=revision,
                                          system_users_id = system_users_id,
                                          timestamp=timestamp,
                                          url='')
                session.add(wbu)

        session.commit()
        return {u'status': 'OK', u'schema': schema}

    # returns a UTC string or None
    def last_tableau_update(self, agent):
        stmt = 'SELECT MAX(updated_at) from workbooks'
        data = agent.odbc.execute(stmt)
        if not data or not '' in data or data[''][0] is None:
            return None
        row = data[''][0]
        if row[0] is None:
            return None
        return row[0]

    # returns a UTC string or None
    def last_update(self):
        envid = self.server.environment.envid
        session = meta.Session()
        value = session.query(func.max(WorkbookEntry.updated_at)).\
                filter(WorkbookEntry.envid == envid).\
                one()
        if value[0] is None:
            return None
        return str(value[0])

    def prune(self, agent):
        """
        If the Tableau Server was restored, there may be revisions in the
        Controller database that no longer exist: remove them.
        """
        last_tableau_update = odbc2dt(self.last_tableau_update(agent))
        if last_tableau_update:
            envid = self.server.environment.envid
            meta.Session.query(WorkbookEntry).\
                filter(WorkbookEntry.updated_at > last_tableau_update).\
                filter(WorkbookEntry.envid == envid).\
                delete(synchronize_session='fetch')
