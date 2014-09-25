from sqlalchemy import Column, String, DateTime, Integer, BigInteger
from sqlalchemy import UniqueConstraint
from sqlalchemy.schema import ForeignKey

# pylint: disable=import-error,no-name-in-module
from akiri.framework.ext.sqlalchemy import meta
# pylint: enable=import-error,no-name-in-module

from httplib import responses

from cache import TableauCacheManager
from mixin import BaseMixin, BaseDictMixin
from http_control import HttpControl
from event_control import EventControl
from util import timedelta_total_seconds
from sites import Site
from workbooks import WorkbookEntry
from profile import UserProfile
from odbc import ODBC

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
    def maxid(cls, envid):
        return cls.max('id', filters={'envid':envid})


class HttpRequestManager(TableauCacheManager):

    def load(self, agent):

        if not self.lock(blocking=False):
            return {u'error': 'Can not load http_requests: busy.'}

        envid = self.server.environment.envid
        self._prune(agent, envid)

        controldata = HttpControl.info()
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
            self.unlock()
            return datadict
        if '' not in datadict:
            self.unlock()
            datadict['error'] = "Missing '' key in query response."
            return datadict

        session = meta.Session()
        for odbcdata in ODBC.load(datadict):
            entry = HttpRequestEntry()
            entry.envid = envid
            odbcdata.copyto(entry)

            system_user_id = userdata.get(entry.site_id, entry.user_id)
            entry.system_user_id = system_user_id

            if not maxid is None: # i.e. not the first import...
                self._test_for_alerts(entry, agent, controldata)
            session.add(entry)
        session.commit()

        self.unlock()
        return {u'status': 'OK', u'count': len(datadict[''])}

    def _test_for_alerts(self, entry, agent, controldata):
        seconds = int(timedelta_total_seconds(entry.completed_at,
                                              entry.created_at))
        body = {'duration':seconds}
        if entry.status >= 400 and entry.action == 'show':
            if entry.status in controldata:
                excludes = controldata[entry.status]
            else:
                excludes = []
            # check the URI against the list to be skipped.
            if not entry.controller in excludes or '*' in excludes:
                self._eventgen(EventControl.HTTP_BAD_STATUS,
                               agent, entry, body=body)
        elif entry.action == 'show' and \
             entry.http_request_uri.startswith('/views/'):
            errorlevel = self.server.system.getint('http-load-error')
            warnlevel = self.server.system.getint('http-load-warn')
            if errorlevel != 0 and seconds >= errorlevel:
                self._eventgen(EventControl.HTTP_LOAD_ERROR,
                               agent, entry, body=body)
            elif warnlevel != 0 and seconds >= warnlevel:
                self._eventgen(EventControl.HTTP_LOAD_WARN,
                               agent, entry, body=body)

    def _get_last_http_requests_id(self, agent):
        stmt = "SELECT MAX(id) FROM http_requests"
        data = agent.odbc.execute(stmt)
        if not data or not '' in data or data[''][0] is None:
            return 0
        row = data[''][0]
        if row[0] is None:
            return 0
        return int(row[0])

    def _parseuri(self, uri, body):
        tokens = uri.split('?', 1)
        if len(tokens) == 2:
            body['uri'] = uri = tokens[0]
            body['query_string'] = tokens[1]
        else:
            body['uri'] = uri
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

    # translate workbook.repository_url -> system_user_id -> owner
    def _translate_workbook(self, body):
        envid = self.server.environment.envid
        url = body['repository_url']
        workbook = WorkbookEntry.get_by_url(envid, url, default=None)
        if not workbook:
            self.server.log.warning("repository_url '%s' Not Found.", url)
            return
        body['workbook'] = workbook.name
        user = UserProfile.get_by_system_user_id(envid, workbook.system_user_id)
        if not user:
            self.server.log.warning("system user '%d' Not Found.",
                                    workbook.system_user_id)
            return
        body['owner'] = user.display_name()

    def _eventgen(self, key, agent, entry, body=None):
        if body is None:
            body = {}
        body = dict(body.items() +\
                        agent.todict().items() +\
                        entry.todict().items())

        self._parseuri(entry.http_request_uri, body)

        body['http_status'] = responses[entry.status]

        system_user_id = entry.system_user_id
        if system_user_id != -1:
            body['system_user_id'] = system_user_id
            body['username'] = \
                self.get_username_from_system_user_id(entry.envid,
                                                      system_user_id)

        if 'repository_url' in body:
            self._translate_workbook(body)

        if entry.site_id and 'site' not in body:
            site = Site.get(entry.envid, entry.site_id)
            if site:
                body['site'] = site.name

        completed_at = entry.completed_at
        self.server.event_control.gen(key, body,
                                      userid=system_user_id,
                                      timestamp=completed_at)

    def _prune(self, agent, envid):
        maxid = self._get_last_http_requests_id(agent)
        meta.Session.query(HttpRequestEntry).\
            filter(HttpRequestEntry.envid == envid).\
            filter(HttpRequestEntry.id > maxid).\
            delete(synchronize_session='fetch')
