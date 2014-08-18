from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy import Integer, BigInteger, SmallInteger
from sqlalchemy import not_
from sqlalchemy.orm.exc import NoResultFound

from akiri.framework.ext.sqlalchemy import meta

from agentinfo import AgentYmlEntry
from cache import TableauCacheManager
from mixin import BaseDictMixin
from http_control import HttpControl
from event_control import EventControl
from util import utc2local, parseutc, DATEFMT
from sites import Site

class HttpRequestEntry(meta.Base, BaseDictMixin):
    __tablename__ = 'http_requests'

    reqid = Column(BigInteger, primary_key=True)
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

    @classmethod
    def get_lastid(cls):
        entry = meta.Session.query(HttpRequestEntry).\
            order_by(HttpRequestEntry.reqid.desc()).first()
        if entry:
            return str(entry.reqid)
        return None


class HttpRequestManager(TableauCacheManager):

    def __init__(self, server):
        self.server = server

    def load(self, agent):
        self.prune(agent)

        stmt = \
            'SELECT id, controller, action, http_referer, http_user_agent, '+\
            'http_request_uri, remote_ip, created_at, session_id, ' +\
            'completed_at, port, user_id, worker, status, '+\
            'user_cookie, user_ip, vizql_session, site_id, currentsheet '+\
            'FROM http_requests '

        session = meta.Session()

        controldata = HttpControl.info()
        cache = self.load_users(agent)

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
            entry = HttpRequestEntry(reqid=row[0],
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

            if entry.status in controldata:
                excludes = controldata[entry.status]
                # check the URI against the list to be skipped.
                if not entry.controller in excludes:
                    self.eventgen(agent, entry, completed_at, cache)

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

    def parseuri(self, body):
        url = body['controller'] # ???
        tokens = url[1:].split('/')
        # /views/<workbook>/<viewname>
        if len(tokens) == 3 and tokens[0].lower() == 'views':
            body['workbook'] = tokens[1]
            body['view'] = tokens[2]
        # /t/<site>/views/<workbook>/<viewname>
        elif len(tokens) == 5 and tokens[0].lower() == 't':
            body['site'] = tokens[1]
            body['workbook'] = tokens[3]
            body['view'] = tokens[4]


    def eventgen(self, agent, entry, completed_at, cache):
        body = dict(agent.todict().items() + entry.todict().items())
        system_user_id = cache.get(entry.site_id, entry.user_id)
        if system_user_id != -1:
            body['system_user_id'] = system_user_id
        url = AgentYmlEntry.get(agent,
                                'svcmonitor.notification.smtp.canonical_url',
                                default=None)
        if url:
            body['tableau_server_url'] = url

        self.parseuri(body)
        if entry.site_id and 'site' not in body:
            site = Site.get(entry.site_id)
            if site:
                body['site'] = site.name

        timestamp=completed_at.strftime(DATEFMT)
        self.server.event_control.gen(EventControl.HTTP_ERROR, body,
                                      userid=system_user_id,
                                      timestamp=completed_at.strftime(DATEFMT))


    def prune(self, agent):
        maxid = self.get_last_http_requests_id(agent)
        meta.Session.query(HttpRequestEntry).\
            filter(HttpRequestEntry.reqid > maxid).\
            delete(synchronize_session='fetch')
