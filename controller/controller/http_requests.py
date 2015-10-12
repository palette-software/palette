from httplib import responses
from urllib import unquote
from urlparse import urlparse

from sqlalchemy import Column, String, DateTime, Integer, BigInteger
from sqlalchemy import UniqueConstraint
from sqlalchemy.schema import ForeignKey
from sqlalchemy.orm.exc import MultipleResultsFound

import akiri.framework.sqlalchemy as meta

from cache import TableauCacheManager
from manager import synchronized
from mixin import BaseMixin, BaseDictMixin
from http_control import HttpControlData
from event_control import EventControl
from util import timedelta_total_seconds, utc2local
from sites import Site
from workbooks import WorkbookEntry
from profile import UserProfile
from odbc import ODBC
from system import SystemKeys

class HttpRequestEntry(meta.Base, BaseMixin, BaseDictMixin):
    __tablename__ = 'http_requests'

    reqid = Column(BigInteger, unique=True, nullable=False,
                   autoincrement=True, primary_key=True)
    envid = Column(BigInteger, ForeignKey("environment.envid"), nullable=False)
    system_user_id = Column(String)
    id = Column(BigInteger, nullable=False)
    controller = Column(String)
    action = Column(String)
    http_referer = Column(String)
    http_user_agent = Column(String)
    http_request_uri = Column(String)
    remote_ip = Column(String)
    created_at = Column(DateTime)
    session_id = Column(String)
    completed_at = Column(DateTime)
    port = Column(Integer)
    user_id = Column(Integer)
    worker = Column(String)
    status = Column(Integer)
    user_cookie = Column(String)
    user_ip = Column(String)
    vizql_session = Column(String)
    site_id = Column(Integer)
    currentsheet = Column(String)

    __table_args__ = (UniqueConstraint('envid', 'id'),)

    @classmethod
    def get_by_vizql_action(cls, envid, vizql_session, action):
        session = meta.Session()

        row = session.query(HttpRequestEntry).\
            filter(HttpRequestEntry.envid == envid).\
            filter(HttpRequestEntry.vizql_session == vizql_session).\
            filter(HttpRequestEntry.action == action).\
            order_by(HttpRequestEntry.created_at.desc()).\
            first()

#        if row == None:
#            print "None found"
#        else:
#            print 'reqid', row.reqid, 'action', row.action,
#            print "http_request_uri = ", row.http_request_uri
#            print "created_at = ", row.created_at
#
        return row

    @classmethod
    def maxid(cls, envid):
        return cls.max('id', filters={'envid':envid})

class HttpRequestManager(TableauCacheManager):

    @synchronized('http_requests')
    def load(self, agent):

        envid = self.server.environment.envid
        self._prune(agent, envid)

        controldata = HttpControlData(self.server)
        userdata = self.load_users(agent)

        maxid = HttpRequestEntry.maxid(envid)
        if maxid is None:
            # our table is empty, just pull in one placeholder record.
            stmt = 'SELECT * FROM http_requests '+\
                   'WHERE id = (SELECT MAX(id) FROM http_requests)'
        else:
            stmt = 'SELECT * FROM http_requests WHERE id > ' + str(maxid)

        datadict = agent.odbc.execute(stmt)
        if 'error' in datadict:
            return datadict
        if '' not in datadict:
            datadict['error'] = "Missing '' key in query response."
            return datadict

        rows = []
        session = meta.Session()
        for odbcdata in ODBC.load(datadict):
            entry = HttpRequestEntry()
            entry.envid = envid
            odbcdata.copyto(entry)

            system_user_id = userdata.get(entry.site_id, entry.user_id)
            entry.system_user_id = system_user_id

            session.add(entry)

            rows.append(entry)

        session.commit()

        # Our table was empty so don't test for alerts on the one
        # placeholder row we brought in.
        if maxid is not None:
            for entry in rows:
#                print "entry: id", entry.id, "action", entry.action,
#                print "vizal_session", entry.vizql_session
                self._test_for_alerts(rows, entry, agent, controldata)

        return {u'status': 'OK', u'count': len(datadict[''])}

    def _parseuri(self, uri, body):
        # Keep body['uri'] to be the whole uri, even if it includes a
        # query string, so query strings can be included in the
        # exclusion matching.
        body['uri'] = uri

        tokens = uri.split('?', 1)
        if len(tokens) == 2:
            body['query_string'] = tokens[1]
        tokens = uri[1:].split('/')
        # /views/<workbook.repository_url>/<viewname>
        if len(tokens) == 3 and tokens[0].lower() == 'views':
            body['repository_url'] = tokens[1]
            body['view'] = tokens[2]
        # /t/<site>/views/<workbook.repository_url>/<viewname>
        elif len(tokens) == 5 and tokens[0].lower() == 't':
            body['site'] = tokens[1]
            body['repository_url'] = tokens[3]
            body['view'] = tokens[4]
        elif len(tokens) >= 7 and tokens[0] == 'vizql':
            # pylint: disable=line-too-long
            # /vizql/t/<site>/w/<workbook.repository_url>/v/<viewname>/performPostLoadOperations...
            #  0     1  2     3         4                 5  6          7
            if tokens[1] == 't' and tokens[3] == 'w' and tokens[5] == 'v':
                body['site'] = tokens[2]
                body['repository_url'] = tokens[4]
                body['view'] = tokens[6]
            # /vizql/w/<workbook.repository_url>/v/<viewname>/bootstrapSession...
            #  0     1               2           3      4         5
            elif tokens[1] == 'w' and tokens[3] == 'v':
                body['repository_url'] = tokens[2]
                body['view'] = tokens[4]

    def _test_for_alerts(self, rows, entry, agent, controldata):
        if entry.http_request_uri.startswith('/admin'):
            return

        body = {}
        self._parseuri(entry.http_request_uri, body)

        if entry.status >= 400 and entry.action == 'show':
            if not controldata.status_exclude(entry.status, body['uri']):
                self._eventgen(EventControl.HTTP_BAD_STATUS,
                               agent, entry, body=body)
        elif entry.action in ('show', 'bootstrapSession',
                                'performPostLoadOperations', 'sessions',
                                'get_customized_views'):
            if controldata.load_exclude(body['uri']):
                return
            self._test_for_load_alerts(rows, entry, agent, body)

    def _test_for_load_alerts(self, rows, entry, agent, body):
    # pylint: disable=too-many-return-statements
    # pylint: disable=too-many-branches
    # Different event types are described in PD-5352.
#        print "action = ", entry.action, "body = ", body

        errorlevel = self.system[SystemKeys.HTTP_LOAD_ERROR]
        warnlevel = self.system[SystemKeys.HTTP_LOAD_WARN]

        if not errorlevel and not warnlevel:
            # alerts for http-requests aren't enabled
            return


#        if entry.action == 'show' and not entry.vizql_session and \
#                                                    not entry.currentsheet:
#            # Type 5
#            self._eventgen(EventControl.HTTP_INITIAL_LOAD_FAILED,
#                               agent, entry, body=body)
#            return

        if entry.action in ('performPostLoadOperations', 'sessions',
                                                'get_customized_views'):
            # Type 2
            seconds = int(timedelta_total_seconds(entry.completed_at,
                                                  entry.created_at))
            body['post_initial_compute'] = seconds
            body['duration'] = seconds  # fixme: remove when event doesn't use

        elif entry.action == 'bootstrapSession':
            if entry.currentsheet and entry.vizql_session:
                # Type 1

                # Remove information from the 'bootstrapSession' row
                # as we will be using the better information from the
                # 'show' row.
                body = {}
                seconds_compute = int(timedelta_total_seconds(
                                      entry.completed_at, entry.created_at))
                body['view_compute_duration'] = seconds_compute

                show_entry = self._find_vizql_entry(rows, entry, 'show')

                if not show_entry:
                    self.server.log.error("http load test Type 1: "
                        "http_requests "
                        "For id %d, action %s, vizql_session %d, did not "
                        "find 'show'",
                        entry.id, entry.action, entry.vizql_session)
                    return

                seconds_load = int(timedelta_total_seconds(
                                   show_entry.completed_at,
                                   show_entry.created_at))
                body['view_load_duration'] = seconds_load

                seconds = body['view_compute_duration'] + \
                                                body['view_load_duration']

                body['total_view_generation_time'] = seconds
                body['duration'] = seconds # fixme: remove when event
                                           # doesn't use
                # For the event, use the action='show' row since it has
                # more information than the action='bootstrapSession' row.
                entry = show_entry
                # Update the body repository_url, view, etc. with the
                # 'show' row.
                self._parseuri(entry.http_request_uri, body)
            elif entry.vizql_session and not entry.currentsheet:
                if entry.status != 500:
                    # At least for now, ignore other http status, such as
                    # 401 which is the embedded password failure.
                    return
                # Type 3
                show_entry = self._find_vizql_entry(rows, entry, 'show')

                if not show_entry:
                    self.server.log.error("http load test Type 3: "
                        "http_requests "
                        "For id %d, action %s, vizql_session %d, did not "
                        "find 'show'",
                        entry.id, entry.action, entry.vizql_session)
                    return

                # Use the information from the 'show' row instead of
                # the 'bootstrapSession' since the 'show' row has more info.
                body = {}
                entry = show_entry
                self._parseuri(entry.http_request_uri, body)
                self._eventgen(EventControl.HTTP_LOAD_TYPE_3,
                               agent, entry, body=body)
                return
#            elif not entry.currentsheet and not entry.vizql_session:
#                # Type 4: currentsheet is blank or empty and vizql_session
#                # is blank or empty
#                self._eventgen(EventControl.HTTP_LOAD_TYPE_4,
#                                   agent, entry, body=body)
#                return
            else:
                self.server.log.debug("http load test: "
                            "http_requests "
                            "For id %d, action %s, currently unhandled "
                            "bootstrapSession case",
                            entry.id, entry.action)
                return

#            print 'found it id:', entry.id, 'action:', entry.action,
#            print ', body:', body, ', seconds:', seconds
        else:
#            print 'ignoring id:', entry.id, 'action:', entry.action,
#            print ', body:', body
            return

#        print 'id:', entry.id, 'action:', entry.action,
#        print 'body:', body, 'seconds:', seconds

        if errorlevel != 0 and seconds >= errorlevel:
            self._eventgen(EventControl.HTTP_LOAD_ERROR,
                           agent, entry, body=body)
        elif warnlevel != 0 and seconds >= warnlevel:
            self._eventgen(EventControl.HTTP_LOAD_WARN,
                           agent, entry, body=body)

    def _find_vizql_entry(self, rows, entry, action):
#        rows = []  # for debugging to remove the cache and force db search
        for row in rows:
            if row.vizql_session == entry.vizql_session and \
                                        row.action == action:
#                print "found it in the cache:", row.reqid
                return row
#            print "not this one. looking for", entry.vizql_session,
#            print "instead it is:", row.reqid, row.vizql_session

        # fixme: search through db
#        return None
#   pylint: disable=unreachable
        # We didn't find it in our latest odbc request so we'll dig through
        # all of the http rows.
        envid = self.server.environment.envid
        db_row = HttpRequestEntry.get_by_vizql_action(envid,
                                                entry.vizql_session, action)
#        if db_row == None:
#            print "Didn't find it in the cache OR db", entry.reqid
#        else:
#            print "Didn't find it in the cache.  db find was:", db_row.reqid
        return db_row

    def _get_last_http_requests_id(self, agent):
        stmt = "SELECT MAX(id) FROM http_requests"
        data = agent.odbc.execute(stmt)
        if not data or not '' in data or data[''][0] is None:
            return 0
        row = data[''][0]
        if row[0] is None:
            return 0
        return int(row[0])

    # translate workbook.repository_url -> system_user_id -> owner
    def _translate_workbook(self, body, entry):
        envid = self.server.environment.envid

        url = body['repository_url']
        try:
            workbook = WorkbookEntry.get_by_url(envid, url, entry.site_id,
                                            default=None)
        except MultipleResultsFound:
            self.server.log.warning(
                    "Multiple rows found for url '%s', site_id: '%s'",
                    url, entry.site_id)
            body['workbook'] = 'Unknown: Duplicate repository url'
            body['owner'] = 'Unknown: Duplicate repository url'
            return

        if not workbook:
            self.server.log.warning("repository_url '%s' Not Found.", url)
            return
        body['workbook'] = workbook.name

        # Send this userid on event generation (workbook owner, not viewer).
        user = UserProfile.get_by_system_user_id(envid, workbook.system_user_id)
        if user:
            body['userid'] = user.userid
            body['owner'] = user.display_name()
        else:
            self.server.log.warning("system user '%d' Not Found.",
                                    workbook.system_user_id)
        body['project'] = workbook.project

        if workbook.site:
            body['site'] = workbook.site
        else:
            if entry.site_id:
                site = Site.get(entry.envid, entry.site_id)
                if site:
                    body['site'] = site.name

    def _eventgen(self, key, agent, entry, body=None):
        if body is None:
            body = {}
        body = dict(body.items() +\
                        agent.todict().items() +\
                        entry.todict().items())

        body['http_status'] = responses[entry.status]

        system_user_id = entry.system_user_id
        if system_user_id != -1:
            profile = UserProfile.get_by_system_user_id(entry.envid,
                                                        entry.system_user_id)
            if profile:
                # This is the browser/viewer user, and not the
                # workbook publisher/owner.
                body['username'] = profile.display_name()

        # An event in the event_control table expects these to exist,
        # but if workbook archiving is off, or the workbook isn't
        # found they will not be set.
        body['owner'] = None
        body['workbook'] = None

        body['userid'] = None       # default

        if 'repository_url' in body:
            self._translate_workbook(body, entry)

        if 'http_referer' in body:
            body['http_referer'] = unquote(body['http_referer']).decode('utf8')

        if 'http_request_uri' in body:
            # Remove query string from the http_request_uri.
            urip = urlparse(body['http_request_uri'])
            http_request_uri = urip.scheme + "://" + urip.netloc + urip.path

            http_request_uri = unquote(http_request_uri)
            body['http_request_uri'] = http_request_uri.decode('utf8')

        userid = body['userid']

        completed_at = utc2local(entry.completed_at)
        self.server.event_control.gen(key, body,
                                      userid=userid,
                                      timestamp=completed_at)

    def _prune(self, agent, envid):
        maxid = self._get_last_http_requests_id(agent)
        meta.Session.query(HttpRequestEntry).\
            filter(HttpRequestEntry.envid == envid).\
            filter(HttpRequestEntry.id > maxid).\
            delete(synchronize_session='fetch')
