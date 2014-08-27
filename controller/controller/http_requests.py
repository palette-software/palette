from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy import Integer, BigInteger, SmallInteger
from sqlalchemy import func, UniqueConstraint, not_
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.schema import ForeignKey

from akiri.framework.ext.sqlalchemy import meta

from agentinfo import AgentYmlEntry
from cache import TableauCacheManager
from mixin import BaseDictMixin
from http_control import HttpControl
from event_control import EventControl
from util import utc2local, parseutc, DATEFMT, timedelta_total_seconds
from sites import Site

class HttpRequestEntry(meta.Base, BaseDictMixin):
    __tablename__ = 'http_requests'


    reqid = Column(BigInteger, unique=True, nullable=False,
                   autoincrement=True, primary_key=True)
    envid = Column(BigInteger, ForeignKey("environment.envid"), nullable=False)
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
        usercache = self.load_users(agent)
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
                                     user_id=row[11],
                                     worker=row[12],
                                     status=row[13],
                                     user_cookie=row[14],
                                     user_ip=row[15],
                                     vizql_session=row[16],
                                     site_id=row[17],
                                     currentsheet=row[18])

            entry.envid = envid
            seconds = timedelta_total_seconds(completed_at, created_at)

            if entry.status >= 400 and entry.action == 'show':
                if entry.status in controldata:
                    excludes = controldata[entry.status]
                else:
                    excludes = []
                # check the URI against the list to be skipped.
                if not entry.controller in excludes:
                    self.eventgen(EventControl.HTTP_BAD_STATUS,
                                  agent, entry, usercache,
                                  body = {'duration':seconds})
            elif entry.action == 'show':
                errorlevel = self.server.system.getint('http-load-error')
                warnlevel = self.server.system.getint('http-load-warn')
                if seconds >= errorlevel:
                    self.eventgen(EventControl.HTTP_LOAD_ERROR,
                                  agent, entry, usercache,
                                  body = {'duration':seconds})
                elif seconds >= warnlevel:
                    self.eventgen(EventControl.HTTP_LOAD_WARN,
                                  agent, entry, usercache,
                                  body = {'duration':seconds})
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

    # translate workbook -> owner_id,site_id -> owner
    def translate_workbook(self, body, usercache):
        name = body['workbook']
        pass

    def eventgen(self, key, agent, entry, usercache, body={}):
        envid = self.server.environment.envid
        body = dict(body.items() +\
                        agent.todict().items() +\
                        entry.todict().items())

        uri = entry.controller # ?!
        self.parseuri(uri, body)

        system_user_id = usercache.get(entry.site_id, entry.user_id)
        if system_user_id != -1:
            body['system_user_id'] = system_user_id
            body['username'] = \
                self.get_username_from_system_user_id(system_user_id)

        if 'workbook' in body:
            self.translate_workbook(body, usercache)

        url = AgentYmlEntry.get(agent,
                                'svcmonitor.notification.smtp.canonical_url',
                                default=None)
        if url:
            body['tableau_server_url'] = url

        if entry.site_id and 'site' not in body:
            site = Site.get(envid, entry.site_id)
            if site:
                body['site'] = site.name

        completed_at = entry.completed_at
        timestamp=completed_at.strftime(DATEFMT)
        self.server.event_control.gen(key, body,
                                      userid=system_user_id,
                                      timestamp=completed_at.strftime(DATEFMT))

    def prune(self, agent):
        maxid = self.get_last_http_requests_id(agent)
        meta.Session.query(HttpRequestEntry).\
            filter(HttpRequestEntry.id > maxid).\
            delete(synchronize_session='fetch')
