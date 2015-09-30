import time
from datetime import datetime

from sqlalchemy import Column, BigInteger, Integer, String, DateTime
from sqlalchemy import UniqueConstraint
from sqlalchemy.schema import ForeignKey

import akiri.framework.sqlalchemy as meta

from event_control import EventControl
from profile import UserProfile
from mixin import BaseMixin, BaseDictMixin
from cache import TableauCacheManager
from manager import synchronized
from odbc import ODBC
from util import timedelta_total_seconds, utc2local
from datasources import DataSourceEntry
from .system import SystemKeys
from workbooks import WorkbookEntry

def to_hhmmss(seconds):
    hours = seconds // (60*60)
    seconds %= (60*60)
    minutes = seconds // 60
    seconds %= 60
    return "%02i:%02i:%02i" % (hours, minutes, seconds)

class ExtractNotification(object):
    EXTRACT_DURATION_WARN = 1 << 0
    EXTRACT_DURATION_ERROR = 1 << 1
    EXTRACT_DELAY_WARN = 1 << 2
    EXTRACT_DELAY_ERROR = 1 << 3

class ExtractEntry(meta.Base, BaseMixin, BaseDictMixin):
    __tablename__ = "extracts"

    extractid = Column(BigInteger, unique=True, nullable=False,
                       primary_key=True)
    envid = Column(BigInteger, ForeignKey("environment.envid"), nullable=False)
    id = Column(BigInteger, nullable=False)
    job_type = Column(String)
    progress = Column(Integer)
    args = Column(String)
    notes = Column(String)
    updated_at = Column(DateTime)
    created_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    job_name = Column(String)
    finish_code = Column(Integer, nullable=False)
    priority = Column(Integer)
    title = Column(String)
    created_on_worker = Column(String)
    processed_on_worker = Column(String)
    link = Column(String)
    lock_version = Column(String)
    backgrounder_id = Column(String)
    site_id = Column(Integer)
    subtitle = Column(String)
    language = Column(String)
    locale = Column(String)
    project_id = Column(Integer)
    system_user_id = Column(Integer)
    notification_state = Column(Integer, default=0)

    __table_args__ = (UniqueConstraint('envid', 'id'),)

    @classmethod
    def get(cls, envid, extract_id, **kwargs):
        keys = {'envid':envid, 'id':extract_id}
        return cls.get_unique_by_keys(keys, **kwargs)

class ExtractManager(TableauCacheManager):

    def _add_info(self, table_class, entry):
        """Look up the extract in the table_class as specified in the args
           column of the passed entry and fill in information, if available,
           for entry attributes such as:
                system_user_id
                project_id
        """
        args = entry.args.split()
        if len(args) < 11 or not args[4].isdigit():
            self.log.error("extract add_info: args bad for %s title %s: %s",
                                table_class.__tablename__,
                                entry.title, entry.args)
            return

        entry_id = int(args[4])
        envid = self.server.environment.envid

        item_entry = table_class.get_newest_by_id(envid, entry_id)
        if not item_entry:
            self.log.error("extract _add_info for %s: No such item "
                           "with title %s, id %d",
                           table_class.__tablename__,
                           entry.title, entry_id)
            return

        entry.system_user_id = item_entry.system_user_id
        entry.project_id = item_entry.project_id

    @synchronized('extracts')
    def load(self, agent, check_odbc_state=True):
        # pylint: disable=too-many-locals
        envid = self.server.environment.envid

        # FIXME
        if check_odbc_state and not self.server.odbc_ok():
            return {"error": "Cannot run command while in state: %s" % \
                        self.server.state_manager.get_state()}

        try:
            self._prune(agent, envid)
        except ValueError as ex:
            self.log.debug(
                "extract prune: Max background job retrieval failed: %s",
                str(ex))
            # The agent probably disconnected
            return {"error": \
                    'max background job retrieval failed: %s' % str(ex)}

        stmt = \
            "SELECT id, job_type, progress, args, notes, finish_code, " +\
            "priority, updated_at, " +\
            " created_at, started_at, completed_at, " +\
            " title, created_on_worker, processed_on_worker, link, " +\
            " lock_version, backgrounder_id, subtitle, language, " +\
            " locale, site_id, job_name " +\
            "FROM background_jobs "

        last_updated_at = self._last_updated_at(envid)
        if last_updated_at is None:
            stmt += "WHERE id = (" +\
                    " SELECT MAX(id) FROM background_jobs " +\
                    " WHERE (job_name = 'Refresh Extracts' " +\
                    "        OR job_name = 'Increment Extracts')" +\
                    ")"
        else:
            stmt += "WHERE (job_name = 'Refresh Extracts' "+\
                    "       OR job_name = 'Increment Extracts') "+\
                    " AND updated_at > '"+\
                    last_updated_at + "'"
        stmt += " ORDER BY id ASC"

        datadict = agent.odbc.execute(stmt)

        if 'error' in datadict or '' not in datadict:
            return datadict

        # Get the tableau system's idea of time which may be different
        # than ours (maybe somebody isn't running ntp or equivalent).
        db_now_utc = self._get_db_now_utc(agent)
        print "db_now_utc = ", db_now_utc

        # Get the latest rows and row updates here
        session = meta.Session()
        for odbcdata in ODBC.load(datadict):
            exid = odbcdata.data['id']
            entry = ExtractEntry.get(envid, exid, default=None)

            if entry is None:
                entry = ExtractEntry(envid=envid)
                session.add(entry)
            odbcdata.copyto(entry)

            data = dict(agent.todict().items())
            self._process(data, db_now_utc, entry)
            session.commit()    # can move this after proven reliable

        self._check_existing_unfinished(agent)

        return {u'status': 'OK', u'count': len(datadict[''])}

    def _check_existing_unfinished(self, agent):
        """Go through our unfinished extracts db to see if any have exceeded
           their start delay or duration thresholds.
        """

        session = meta.Session()
        rows = session.query(ExtractEntry).\
            filter(ExtractEntry.progress != 100).\
            all()

        db_now_utc = self._get_db_now_utc(agent)

        for row in rows:
            data = dict(agent.todict().items())
            self._process(data, db_now_utc, row)
            session.commit()    # can move this after proven reliable

    # Fixme: Move to a general db file
    def _get_db_now_utc(self, agent):
        """
            Get the tableau postgres database's idea of the current
            time which may differ from our idea of the current time.
        """
        stmt = "select now()"
        datadict = agent.odbc.execute(stmt)

        if 'error' in datadict or '' not in datadict:
            return datadict

        time_rows = datadict['']
        if not len(time_rows) or not len(time_rows[0]):
            self.log.error("extract load.  Missing db time now: %s", time_rows)
            return datetime.utcnow()

        # Comes back something like "2015-09-29 18:19:08.156985+00"
        time_str = time_rows[0][0]
        if time_str.find('.'):
            time_str = time_str.split('.')[0]
        try:
            struct = time.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            self.log.error("extract load.  Bad db now: %s", time_str)
            return datetime.utcnow()

        return datetime.fromtimestamp(time.mktime(struct))

    def _process(self, data, db_now_utc, entry):
        """Send events are appropriate:
            - delayed start
            - duration exeeded
            - EXTRACT OK
            - EXTRACT FAILED
        """
        if entry.notification_state is None:
            entry.notification_stateis = 0

        if not entry.started_at:
            self._check_start_delay(data, db_now_utc, entry)
        else:
            self._check_duration_exceeded(data, db_now_utc, entry)

        self._check_finished(data, entry)

    def _check_start_delay(self, data, db_now_utc, entry):
        """Check for delayed start time.
           Sends an event on start time exceeded.
        """
        time_since_created = timedelta_total_seconds(db_now_utc,
                                                        entry.created_at)
        print "-----------time_since_created:", time_since_created, entry.title
        # Check to see if the extract STARTED late.
        if self.system[SystemKeys.EXTRACT_DELAY_ERROR] and \
                (time_since_created >= \
                    self.system[SystemKeys.EXTRACT_DELAY_ERROR]) and \
                        not entry.notification_state & \
                            ExtractNotification.EXTRACT_DELAY_ERROR:
            data['extract_delay_seconds'] = time_since_created
            self._eventgen(EventControl.EXTRACT_DELAY_ERROR, data, entry)
            entry.notification_state |= \
                                    ExtractNotification.EXTRACT_DELAY_ERROR
        elif self.system[SystemKeys.EXTRACT_DELAY_WARN] and \
                    (time_since_created >= \
                        self.system[SystemKeys.EXTRACT_DELAY_WARN]) and \
                            not entry.notification_state & \
                                (ExtractNotification.EXTRACT_DELAY_WARN | \
                                ExtractNotification.EXTRACT_DELAY_ERROR):
            # Note: We don't send a WARN event if we already sent an ERROR
            data['extract_delay_seconds'] = time_since_created
            self._eventgen(EventControl.EXTRACT_DURATION_WARN, data, entry)
            entry.notification_state |= ExtractNotification.EXTRACT_DELAY_WARN


    def _check_duration_exceeded(self, data, db_now_utc, entry):
        """Called when there is a "started_at" value.
            There is a started_at, and may or not be a completed_at.
            Sends an event if the extract ran too long.
        """
        if entry.completed_at:
            run_time = timedelta_total_seconds(entry.completed_at,
                                                           entry.started_at)
        else:
            # Compute how long it's been running so far
            run_time = int((db_now_utc - entry.started_at).\
                            total_seconds())
        print "run_time:", run_time, entry.title
        if self.system[SystemKeys.EXTRACT_DURATION_ERROR] and \
                (run_time >=
                    self.system[SystemKeys.EXTRACT_DURATION_ERROR]) and \
                        not entry.notification_state & \
                            ExtractNotification.EXTRACT_DURATION_ERROR:
            data['extract_duration_seconds'] = run_time
            self._eventgen(EventControl.EXTRACT_DURATION_ERROR, data, entry)
            entry.notification_state |= \
                                ExtractNotification.EXTRACT_DURATION_ERROR
        elif self.system[SystemKeys.EXTRACT_DURATION_WARN] and \
                (run_time >= \
                            self.system[SystemKeys.EXTRACT_DURATION_WARN]) and \
                        not entry.notification_state & \
                            (ExtractNotification.EXTRACT_DURATION_WARN |
                             ExtractNotification.EXTRACT_DURATION_ERROR):
            # Note: We don't send a WARN event if we already sent an ERROR
            data['extract_duration_seconds'] = run_time
            self._eventgen(EventControl.EXTRACT_DURATION_WARN, data, entry)
            entry.notification_state |= \
                                ExtractNotification.EXTRACT_DURATION_WARN

    def _check_finished(self, data, entry):
        """If the extract finished, send an event as appropriate:
            EXTRACT-OK
            EXTRACT-FAILED
        """
        if entry.completed_at is None or entry.started_at is None:
            return

        if entry.finish_code == 0:
            self._eventgen(EventControl.EXTRACT_OK, data, entry)
        else:
            self._eventgen(EventControl.EXTRACT_FAILED, data, entry)

    def _last_updated_at(self, envid):
        """ Returns None if the table is empty."""
        value = ExtractEntry.max('updated_at', filters={'envid':envid})
        if value is None:
            return None
        return str(value)

    def _last_background_jobs_id(self, agent):
        stmt = "SELECT MAX(id) FROM background_jobs"
        data = agent.odbc.execute(stmt)
        if 'error' in data:
            raise ValueError(data['error'])
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
            filter(ExtractEntry.id > maxid).\
            delete(synchronize_session='fetch')

    # FIXME: add project_id? maybe job_name?
    def _eventgen(self, key, data, entry):
        # Placeholder to be set by the next functions.
        entry.system_user_id = -1

        if entry.subtitle == 'Workbook':
            self._add_info(WorkbookEntry, entry)
        if entry.subtitle in ('Data Source', 'Datasource',
                              'RefreshExtractTask'):
            self._add_info(DataSourceEntry, entry)

        data = dict(data.items() + entry.todict().items())

        self._add_minutes(data)
        if entry.completed_at is not None and entry.started_at is not None:
            duration = timedelta_total_seconds(entry.completed_at,
                                               entry.started_at)
            data['duration'] = duration
            data['duration_hms'] = to_hhmmss(duration)
            timestamp = utc2local(entry.completed_at)
        else:
            timestamp = None

        envid = self.server.environment.envid
        profile = UserProfile.get_by_system_user_id(envid,
                                                    data['system_user_id'])
        if profile:
            data['username'] = profile.display_name()
            userid = profile.userid
        else:
            data['username'] = "Unknown User"
            userid = None

        self.server.event_control.gen(key, data,
                                             userid=userid,
                                             site_id=data['site_id'],
                                             timestamp=timestamp)

    def _add_minutes(self, data):
        """Add extract_delay/duration_warn/error_minutes to the
           data dictionary.
        """
        if self.system[SystemKeys.EXTRACT_DELAY_WARN]:
            data['extract_delay_warn_minutes'] = \
                        self.system[SystemKeys.EXTRACT_DELAY_WARN] / 60
        if self.system[SystemKeys.EXTRACT_DELAY_ERROR]:
            data['extract_delay_error_minutes'] = \
                        self.system[SystemKeys.EXTRACT_DELAY_ERROR] / 60

        if self.system[SystemKeys.EXTRACT_DURATION_WARN]:
            data['extract_duration_warn_minutes'] = \
                        self.system[SystemKeys.EXTRACT_DURATION_WARN] / 60
        if self.system[SystemKeys.EXTRACT_DURATION_ERROR]:
            data['extract_duration_error_minutes'] = \
                        self.system[SystemKeys.EXTRACT_DURATION_ERROR] / 60

    @classmethod
    def publishers(cls):
        query = meta.Session.query(UserProfile).\
            join(ExtractEntry,
                 UserProfile.system_user_id == ExtractEntry.system_user_id)
        return query.all()
