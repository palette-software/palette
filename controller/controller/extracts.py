import time
from datetime import datetime

from sqlalchemy import Column, BigInteger, Integer, String, DateTime
from sqlalchemy.schema import ForeignKey
from sqlalchemy.orm.exc import NoResultFound

from akiri.framework.ext.sqlalchemy import meta

from event_control import EventControl
from profile import UserProfile
from mixin import BaseDictMixin
from util import utc2local, parseutc, DATEFMT
from cache import TableauCacheManager

def to_hhmmss(td):
    seconds = td.seconds
    hours = seconds // (60*60)
    seconds %= (60*60)
    minutes = seconds // 60
    seconds %= 60
    return "%02i:%02i:%02i" % (hours, minutes, seconds)

class ExtractEntry(meta.Base, BaseDictMixin):
    __tablename__ = "extracts"

    extractid = Column(BigInteger, unique=True, nullable=False,
                       primary_key=True)
    agentid = Column(BigInteger, ForeignKey("agent.agentid"), nullable=False)
    finish_code = Column(Integer, nullable=False)
    notes = Column(String)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    title = Column(String)
    subtitle = Column(String)
    site_id = Column(Integer)
    project_id = Column(Integer)
    system_users_id = Column(Integer)
    job_name = Column(String)


class ExtractManager(TableauCacheManager):

    def __init__(self, server):
        self.server = server

    def workbook_update(self, agent, entry, users, cache={}):
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

        entry.system_users_id = users.get(row[1], row[0])
        entry.project_id = int(row[2])

    # FIXME: merge the update functions
    def datasource_update(self, agent, entry, users, cache={}):
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

        entry.system_users_id = users.get(row[1], row[0])
        entry.project_id = int(row[2])

    def load(self, agent):

        # FIXME
        if not self.server.odbc_ok():
            return {"error": "Cannot run command while in state: %s" % \
                        self.server.stateman.get_state()}

        self.prune(agent)

        stmt = "SELECT id, finish_code, notes, started_at, completed_at, "+\
            "title, subtitle, site_id, job_name " +\
            "FROM background_jobs " +\
            "WHERE (job_name = 'Refresh Extracts' "+\
            " OR job_name = 'Increment Extracts') AND progress = 100"

        session = meta.Session()

        lastid = self.get_lastid()
        if not lastid is None:
            stmt += " AND id > " + lastid

        stmt += " ORDER BY id ASC"

        data = agent.odbc.execute(stmt)

        if 'error' in data or '' not in data:
            return data

        datasources = {}
        workbooks = {}
        users = self.load_users(agent)

        for row in data['']:
            started_at = utc2local(parseutc(row[3]))
            completed_at = utc2local(parseutc(row[4]))
            entry = ExtractEntry(extractid=row[0],
                                 agentid=agent.agentid,
                                 finish_code=row[1],
                                 notes=row[2],
                                 started_at=started_at,
                                 completed_at=completed_at,
                                 title=row[5],
                                 subtitle=row[6],
                                 site_id=row[7],
                                 job_name=row[8])

            # Placeholder to be set by the next functions.
            entry.system_users_id = -1

            if entry.subtitle == 'Workbook':
                self.workbook_update(agent, entry, users, cache=workbooks)
            if entry.subtitle == 'Data Source':
                self.datasource_update(agent, entry, users, cache=datasources)

            body = dict(agent.todict().items() + entry.todict().items())

            if row[3] is not None and row[4] is not None:
                duration = parseutc(row[4]) - parseutc(row[3])
                body['duration'] = duration.seconds
                duration_hms = to_hhmmss(duration)
                body['duration_hms'] = str(duration_hms)

            if entry.finish_code == 0:
                self.eventgen(EventControl.EXTRACT_OK, body,
                              timestamp=completed_at.strftime(DATEFMT))
            else:
                self.eventgen(EventControl.EXTRACT_FAILED, body,
                              timestamp=completed_at.strftime(DATEFMT))

            session.add(entry)

        session.commit()

        return {u'status': 'OK',
                u'count': len(data[''])}

    # FIXME: user agentid
    # FIXME: use MAX()
    def get_lastid(self):
        entry = meta.Session.query(ExtractEntry).\
            order_by(ExtractEntry.extractid.desc()).first()
        if entry:
                return str(entry.extractid)
        return None

    def get_last_background_jobs_id(self, agent):
        stmt = "SELECT MAX(id) FROM background_jobs"
        data = agent.odbc.execute(stmt)
        if not data or not '' in data or data[''][0] is None:
            return 0
        row = data[''][0]
        if row[0] is None:
            return 0
        return int(row[0])

    def prune(self, agent):
        """
        If the Tableau Server was restored, there may be events in the
        Controller database that no longer exist: remove them.
        """
        maxid = self.get_last_background_jobs_id(agent)
        meta.Session.query(ExtractEntry).\
            filter(ExtractEntry.extractid > maxid).\
            delete(synchronize_session='fetch')

    # FIXME: add project_id? maybe job_name?
    def eventgen(self, key, data, timestamp=None):
        system_user_id = data['system_users_id']
        data['username'] = \
            self.get_username_from_system_user_id(system_user_id)

        return self.server.event_control.gen(key, data,
                                             userid=data['system_users_id'],
                                             siteid=data['site_id'],
                                             timestamp=timestamp)

    @classmethod
    def publishers(cls):
        query = meta.Session.query(UserProfile).\
            join(ExtractEntry,
                 UserProfile.system_users_id == ExtractEntry.system_users_id)
        return query.all()
