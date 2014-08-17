from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy import Integer, BigInteger, SmallInteger
from sqlalchemy import not_
from sqlalchemy.orm.exc import NoResultFound

from akiri.framework.ext.sqlalchemy import meta

from mixin import BaseDictMixin
from http_control import HttpControl
from event_control import EventControl

from util import utc2local, parseutc, DATEFMT

class HTTPRequestEntry(meta.Base, BaseDictMixin):
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
        entry = meta.Session.query(HTTPRequestEntry).\
            order_by(HTTPRequestEntry.reqid.desc()).first()
        if entry:
            return str(entry.reqid)
        return None

    @classmethod
    def eventgen(cls, agent, entry, completed_at):
        body = dict(agent.todict().items() + entry.todict().items())
        timestamp=completed_at.strftime(DATEFMT)
        agent.server.event_control.gen(EventControl.HTTP_ERROR, body,
                                       timestamp=completed_at.strftime(DATEFMT))

    @classmethod
    def load(cls, agent):
        cls.prune(agent)

        stmt = \
            'SELECT id, controller, action, http_referer, http_user_agent, '+\
            'http_request_uri, remote_ip, created_at, session_id, ' +\
            'completed_at, port, user_id, worker, status, '+\
            'user_cookie, user_ip, vizql_session, site_id, currentsheet '+\
            'FROM http_requests '

        session = meta.Session()

        controldata = HttpControl.info()

        lastid = cls.get_lastid()
        if not lastid is None:
            stmt += "WHERE id > " + lastid

        data = agent.odbc.execute(stmt)
        if 'error' in data:
            return data
        if '' not in data:
            data['error'] = "Missing '' key in query response."

        for row in data['']:
            created_at = utc2local(parseutc(row[7]))
            completed_at = utc2local(parseutc(row[9]))
            entry = HTTPRequestEntry(reqid=row[0],
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
                    cls.eventgen(agent, entry, completed_at)

            session.add(entry)

        session.commit()

        d = {u'status': 'OK', u'count': len(data[''])}
        return d

    @classmethod
    def get_last_http_requests_id(cls, agent):
        stmt = "SELECT MAX(id) FROM http_requests"
        data = agent.odbc.execute(stmt)
        if not data or not '' in data or data[''][0] is None:
            return 0
        row = data[''][0]
        if row[0] is None:
            return 0
        return int(row[0])

    @classmethod
    def prune(cls, agent):
        maxid = cls.get_last_http_requests_id(agent)
        meta.Session.query(HTTPRequestEntry).\
            filter(HTTPRequestEntry.reqid > maxid).\
            delete(synchronize_session='fetch')
