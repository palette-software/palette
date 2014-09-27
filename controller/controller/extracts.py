from sqlalchemy import Column, BigInteger, Integer, String, DateTime
from sqlalchemy.schema import ForeignKey

from sqlalchemy import UniqueConstraint

# pylint: disable=import-error,no-name-in-module
from akiri.framework.ext.sqlalchemy import meta
# pylint: enable=import-error,no-name-in-module

from event_control import EventControl
from profile import UserProfile
from mixin import BaseMixin, BaseDictMixin
from cache import TableauCacheManager
from manager import synchronized
from odbc import ODBC
from util import timedelta_total_seconds

def to_hhmmss(seconds):
    hours = seconds // (60*60)
    seconds %= (60*60)
    minutes = seconds // 60
    seconds %= 60
    return "%02i:%02i:%02i" % (hours, minutes, seconds)

class ExtractEntry(meta.Base, BaseMixin, BaseDictMixin):
    __tablename__ = "extracts"

    extractid = Column(BigInteger, unique=True, nullable=False,
                       primary_key=True)
    envid = Column(BigInteger, ForeignKey("environment.envid"), nullable=False)
    id = Column(BigInteger, nullable=False)
    args = Column(String)
    notes = Column(String)
    finish_code = Column(Integer, nullable=False)
    priority = Column(Integer)
    updated_at = Column(DateTime)
    created_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    title = Column(String)
    created_on_worker = Column(String)
    processed_on_worker = Column(String)
    link = Column(String)
    lock_version = Column(String)
    backgrounder_id = Column(String)
    subtitle = Column(String)
    language = Column(String)
    locale = Column(String)
    site_id = Column(Integer)
    project_id = Column(Integer)
    system_user_id = Column(Integer)
    job_name = Column(String)

    __table_args__ = (UniqueConstraint('envid', 'id'),)


class ExtractManager(TableauCacheManager):

    def workbook_update(self, agent, entry, users, cache=None):
        if cache is None:
            cache = {}
        title = entry.title.replace("'", "''")
        stmt = \
            "SELECT owner_id, site_id, project_id " +\
            "FROM workbooks WHERE name = '%s'"
        stmt = stmt % (title,)

        if entry.title in cache:
            row = cache[entry.title]
        else:
            data = agent.odbc.execute(stmt)
            if 'error' in data or '' not in data or not data['']:
                return  # FIXME: log
            row = cache[entry.title] = data[''][0]

        entry.system_user_id = users.get(row[1], row[0])
        entry.project_id = int(row[2])

    # FIXME: merge the update functions
    def datasource_update(self, agent, entry, users, cache=None):
        if cache is None:
            cache = {}
        title = entry.title.replace("'", "''")
        stmt = \
            "SELECT owner_id, site_id, project_id " +\
            "FROM datasources WHERE name = '%s'"
        stmt = stmt % (title,)

        if entry.title in cache:
            row = cache[entry.title]
        else:
            data = agent.odbc.execute(stmt)
            if 'error' in data or '' not in data or not data['']:
                return # FIXME: log
            row = cache[entry.title] = data[''][0]

        entry.system_user_id = users.get(row[1], row[0])
        entry.project_id = int(row[2])

    @synchronized('extracts')
    def load(self, agent, check_odbc_state=True):
        envid = self.server.environment.envid

        # FIXME
        if check_odbc_state and not self.server.odbc_ok():
            return {"error": "Cannot run command while in state: %s" % \
                        self.server.state_manager.get_state()}

        self._prune(agent, envid)

        stmt = \
            "SELECT id, args, notes, finish_code, priority, updated_at, " +\
            " created_at, started_at, completed_at, "+\
            " title, created_on_worker, processed_on_worker, link, " +\
            " lock_version, backgrounder_id, subtitle, language, " +\
            " locale, site_id, job_name " +\
            "FROM background_jobs "

        last_completed_at = self._last_completed_at(envid)
        if last_completed_at is None:
            stmt += "WHERE id = (" +\
                    " SELECT MAX(id) FROM background_jobs " +\
                    " WHERE (job_name = 'Refresh Extracts' "+\
                    "        OR job_name = 'Increment Extracts') "+\
                    "  AND progress = 100)"
        else:
            stmt += "WHERE (job_name = 'Refresh Extracts' "+\
                    "       OR job_name = 'Increment Extracts') "+\
                    " AND progress = 100 AND completed_at > '"+\
                    last_completed_at + "'"
        stmt += " ORDER BY id ASC"


        datadict = agent.odbc.execute(stmt)

        if 'error' in datadict or '' not in datadict:
            return datadict

        datasources = {}
        workbooks = {}
        userdata = self.load_users(agent)

        session = meta.Session()
        for odbcdata in ODBC.load(datadict):
            entry = ExtractEntry()
            entry.envid = envid
            odbcdata.copyto(entry)

            # Placeholder to be set by the next functions.
            entry.system_user_id = -1

            if entry.subtitle == 'Workbook':
                self.workbook_update(agent, entry, userdata, cache=workbooks)
            if entry.subtitle == 'Data Source':
                self.datasource_update(agent, entry, userdata,
                                       cache=datasources)
            body = dict(agent.todict().items() + entry.todict().items())

            if entry.completed_at is not None and entry.started_at is not None:
                duration = timedelta_total_seconds(entry.completed_at,
                                                   entry.started_at)
                body['duration'] = duration
                body['duration_hms'] = to_hhmmss(duration)

            if entry.finish_code == 0:
                self._eventgen(EventControl.EXTRACT_OK, body,
                               timestamp=entry.completed_at)
            else:
                self._eventgen(EventControl.EXTRACT_FAILED, body,
                               timestamp=entry.completed_at)

            session.add(entry)

        session.commit()
        return {u'status': 'OK', u'count': len(datadict[''])}

    # Returns None if the table is empty.
    def _last_completed_at(self, envid):
        value = ExtractEntry.max('completed_at', filters={'envid':envid})
        if value is None:
            return None
        return str(value)


    def _last_background_jobs_id(self, agent):
        stmt = "SELECT MAX(id) FROM background_jobs"
        data = agent.odbc.execute(stmt)
        if not data or not '' in data or data[''][0] is None:
            return 0
        row = data[''][0]
        if row[0] is None:
            return 0
        return int(row[0])

    def _prune(self, agent, envid):
        """
        If the Tableau Server was restored, there may be events in the
        Controller database that no longer exist: remove them.
        """
        maxid = self._last_background_jobs_id(agent)
        meta.Session.query(ExtractEntry).\
            filter(ExtractEntry.envid == envid).\
            filter(ExtractEntry.extractid > maxid).\
            delete(synchronize_session='fetch')

    # FIXME: add project_id? maybe job_name?
    def _eventgen(self, key, data, timestamp=None):
        envid = self.server.environment.envid
        system_user_id = data['system_user_id']
        data['username'] = \
            self.get_username_from_system_user_id(envid, system_user_id)

        return self.server.event_control.gen(key, data,
                                             userid=data['system_user_id'],
                                             siteid=data['site_id'],
                                             timestamp=timestamp)

    @classmethod
    def publishers(cls):
        query = meta.Session.query(UserProfile).\
            join(ExtractEntry,
                 UserProfile.system_user_id == ExtractEntry.system_user_id)
        return query.all()
