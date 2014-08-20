import time
from sqlalchemy import Column, BigInteger, Integer, Boolean, String, DateTime
from sqlalchemy import func, UniqueConstraint
from sqlalchemy.schema import ForeignKey
from sqlalchemy.orm.exc import NoResultFound

from akiri.framework.ext.sqlalchemy import meta

from cache import TableauCacheManager
from util import odbc2dt

class WorkbookEntry(meta.Base):
    __tablename__ = "workbooks"

    workbookid = Column(BigInteger, unique=True, nullable=False,
                        autoincrement=True, primary_key=True)
    agentid = Column(BigInteger, ForeignKey("agent.agentid"), nullable=False)
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
    revision = Column(String, nullable=False)
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

    __table_args__ = (UniqueConstraint('agentid', 'id', 'revision'),)

class WorkbookManager(TableauCacheManager):

    def __init__(self, server):
        self.server = server

    def entry(self, agentid, id, revision, **kwargs):
        if 'default' in kwargs:
            default = kwargs['default']
            have_default = True
            del kwargs['default']
        else:
            have_default = False

        if kwargs:
            raise ValueError("Invalid kwargs")

        try:
            entry = meta.Session.query(WorkbookEntry).\
                filter(WorkbookEntry.agentid == agentid).\
                filter(WorkbookEntry.id == id).\
                filter(WorkbookEntry.revision == revision).\
                one()
        except NoResultFound, e:
            if have_default:
                return default
            raise ValueError("No workbook (%d,'%s')" % (id, revision))
        return entry


    def load(self, agent):
        self.prune(agent)

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

        last_update = self.last_update(agent)
        if last_update:
            stmt += " WHERE updated_at > '" + last_update + "'"

        data = agent.odbc.execute(stmt)

        schema = self.schema(data)

        if 'error' in data or '' not in data:
            return data

        for row in data['']:
            entryid = row[0]
            revision = row[22]
            entry = self.entry(agent.agentid, entryid, revision, default=None)
            if entry is None:
                entry = WorkbookEntry(agentid=agent.agentid,
                                      id=entryid, revision=revision)
                session.add(entry)

            entry.name = row[1]
            entry.repository_url = row[2]
            entry.description = row[3]
            entry.created_at = odbc2dt(row[4])
            entry.updated_at = odbc2dt(row[5])
            entry.owner_id = row[6]
            entry.project_id = row[7]
            entry.view_count = row[8]
            entry.size = row[9]
            entry.embedded = row[10]
            entry.thumb_user = row[11]
            entry.refreshable_extracts = row[12]
            entry.extracts_refreshed_at = odbc2dt(row[13])
            entry.lock_version = row[14]
            entry.state = row[15]
            entry.version = row[16]
            entry.checksum = row[17]
            entry.display_tabs = row[18]
            entry.data_engine_extracts = row[19]
            entry.incrementable_extracts = row[20]
            entry.site_id = row[21]
            entry.repository_data_id = row[23]
            entry.repository_extract_data_id = row[24]
            entry.first_published_at = odbc2dt(row[25])
            entry.primary_content_url = row[26]
            entry.share_description = row[27]
            entry.show_toolbar = row[28]
            entry.extracts_incremented_at = odbc2dt(row[29])
            entry.default_view_index = row[30]
            entry.luid = row[31]
            entry.asset_key_id = row[32]
            entry.document_version = row[33]

        session.commit()

        return {u'status': 'OK', u'schema': schema,
                u'count': len(data[''])}

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
    def last_update(self, agent):
        value = meta.Session.query(func.max(WorkbookEntry.updated_at)).one()
        if value[0] is None:
            return None
        return str(value[0])

    def prune(self, agent):
        """
        If the Tableau Server was restored, there may be revisions in the
        Controller database that no longer exist: remove them.
        """
        last_update = self.last_tableau_update(agent)
        if last_update:
            meta.Session.query(WorkbookEntry).\
                filter(WorkbookEntry.updated_at > last_update).\
                delete(synchronize_session='fetch')
