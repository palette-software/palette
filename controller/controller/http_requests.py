from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy import Integer, BigInteger, SmallInteger
from sqlalchemy import func, UniqueConstraint, not_
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.schema import ForeignKey

from akiri.framework.ext.sqlalchemy import meta
from httplib import responses

from cache import TableauCacheManager
from mixin import BaseDictMixin
from http_control import HttpControl
from event_control import EventControl
from util import utc2local, parseutc, DATEFMT, timedelta_total_seconds
from sites import Site
from workbooks import WorkbookEntry
from profile import UserProfile

class HttpRequestEntry(meta.Base, BaseDictMixin):
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
    def get_lastid(cls):
        entry = meta.Session.query(HttpRequestEntry).\
            order_by(HttpRequestEntry.id.desc()).first()
        if entry:
            return str(entry.id)
        return None

class HttpRequestManager(TableauCacheManager):

    def load(self, agent):
        envid = self.server.environment.envid
        self.prune(agent)

        stmt = \
            'SELECT id, controller, action, http_referer, http_user_agent, '+\
            'http_request_uri, remote_ip, created_at, session_id, ' +\
            'completed_at, port, user_id, worker, status, '+\
            'user_cookie, user_ip, vizql_session, site_id, currentsheet '+\
            'FROM http_requests '

        session = meta.Session()

        controldata = HttpControl.info()
        users = self.load_users(agent)
        lastid = HttpRequestEntry.get_lastid()
        if not lastid is None:
            stmt += 'WHERE id > ' + str(lastid)

        data = agent.odbc.execute(stmt)
        if 'error' in data:
            return data
        if '' not in data:
            data['error'] = "Missing '' key in query response."

        for row in data['']:
            created_at = utc2local(parseutc(row[7]))
            completed_at = utc2local(parseutc(row[9]))

            user_id = row[11]
            site_id = row[17]
            system_user_id = users.get(site_id, user_id)

            entry = HttpRequestEntry(id=row[0],
                                     controller=row[1],
                                     action = row[2],
                                     http_referer=row[3],
                                     http_user_agent=row[4],
                                     http_request_uri=row[5],
                                     remote_ip=row[6],
                                     created_at=created_at,
                                     session_id=row[8],
                                     completed_at=completed_at,
                                     port=row[10],
                                     user_id=user_id,
                                     worker=row[12],
                                     status=row[13],
                                     user_cookie=row[14],
                                     user_ip=row[15],
                                     vizql_session=row[16],
                                     site_id=site_id,
                                     currentsheet=row[18])

            entry.envid = envid
            entry.system_user_id = system_user_id
            seconds = int(timedelta_total_seconds(completed_at, created_at))

            if entry.status >= 400 and entry.action == 'show':
                if entry.status in controldata:
                    excludes = controldata[entry.status]
                else:
                    excludes = []
                # check the URI against the list to be skipped.
                if not entry.controller in excludes:
                    body =  {'duration':seconds, 'http_status': responses[entry.status]}
                    self.eventgen(EventControl.HTTP_BAD_STATUS,
                                  agent, entry, body=body)
            elif entry.action == 'show':
                errorlevel = self.server.system.getint('http-load-error')
                warnlevel = self.server.system.getint('http-load-warn')
                if errorlevel != 0 and seconds >= errorlevel:
                    body =  {'duration':seconds, 'http_status': responses[entry.status]}
                    self.eventgen(EventControl.HTTP_LOAD_ERROR,
                                  agent, entry, body=body)
                elif warnlevel != 0 and seconds >= warnlevel:
                    body =  {'duration':seconds, 'http_status': responses[entry.status]}
                    self.eventgen(EventControl.HTTP_LOAD_WARN,
                                  agent, entry, body=body)
            session.add(entry)

        session.commit()

        d = {u'status': 'OK', u'count': len(data[''])}
        return d


    def get_last_http_requests_id(self, agent):
        stmt = "SELECT MAX(id) FROM http_requests"
        data = agent.odbc.execute(stmt)
        if not data or not '' in data or data[''][0] is None:
            return 0
        row = data[''][0]
        if row[0] is None:
            return 0
        return int(row[0])

    def parseuri(self, uri, body):
        tokens = uri.split('?', 1)
        if len(tokens) == 2:
            body['uri'] = uri = tokens[0]
            body['query_string'] = tokens[1]
        else:
            body['uri'] = uri
        tokens = uri[1:].split('/')
        # /views/<workbook>/<viewname>
        if len(tokens) == 3 and tokens[0].lower() == 'views':
            body['workbook'] = tokens[1]
            body['view'] = tokens[2]
        # /t/<site>/views/<workbook>/<viewname>
        elif len(tokens) == 5 and tokens[0].lower() == 't':
            body['site'] = tokens[1]
            body['workbook'] = tokens[3]
            body['view'] = tokens[4]

    # translate workbook.name -> system_user_id -> owner
    def translate_workbook(self, body):
        envid = self.server.environment.envid
        name = body['workbook']
        workbook = WorkbookEntry.get(envid, name, default=None)
        if not workbook:
            return
        user = UserProfile.get_by_system_user_id(envid, workbook.system_user_id)
        if not user:
            return
        body['owner'] = user.display_name()

    def eventgen(self, key, agent, entry, body={}):
        body = dict(body.items() +\
                        agent.todict().items() +\
                        entry.todict().items())

        self.parseuri(entry.http_request_uri, body)

        system_user_id = entry.system_user_id
        if system_user_id != -1:
            body['system_user_id'] = system_user_id
            body['username'] = \
                self.get_username_from_system_user_id(entry.envid,
                                                      system_user_id)

        if 'workbook' in body:
            self.translate_workbook(body)

        if entry.site_id and 'site' not in body:
            site = Site.get(entry.envid, entry.site_id)
            if site:
                body['site'] = site.name

        completed_at = entry.completed_at
        timestamp=completed_at.strftime(DATEFMT)
        self.server.event_control.gen(key, body,
                                      userid=system_user_id,
                                      timestamp=completed_at)

    def prune(self, agent):
        maxid = self.get_last_http_requests_id(agent)
        meta.Session.query(HttpRequestEntry).\
            filter(HttpRequestEntry.id > maxid).\
            delete(synchronize_session='fetch')
