from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy import Integer, BigInteger, SmallInteger
from sqlalchemy import not_
from sqlalchemy.orm.exc import NoResultFound

from akiri.framework.ext.sqlalchemy import meta

class HTTPRequestEntry(meta.Base):
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
    def load(cls, agent):
        cls.prune(agent)

        stmt = \
            'SELECT id, controller, action, http_referer, http_user_agent, '+\
            'http_request_uri, remote_ip, created_at, session_id, ' +\
            'completed_at, port, user_id, worker, status, '+\
            'user_cookie, user_ip, vizql_session, site_id, currentsheet '+\
            'FROM http_requests '

        session = meta.Session()

        lastid = cls.get_lastid()
        if not lastid is None:
            stmt += "WHERE id > " + lastid

        data = agent.odbc.execute(stmt)
        if 'error' in data:
            return data
        if '' not in data:
            data['error'] = "Missing '' key in query response."

        for row in data['']:
            entry = HTTPRequestEntry(reqid=row[0],
                                     controller=row[1],
                                     action = row[2],
                                     http_referer=row[3],
                                     http_user_agent=row[4],
                                     http_request_uri=row[5],
                                     remote_ip=row[6],
                                     created_at=row[7],
                                     session_id=row[8],
                                     completed_at=row[9],
                                     port=row[10],
                                     user_id=row[11],
                                     worker=row[12],
                                     status=row[13],
                                     user_cookie=row[14],
                                     user_ip=row[15],
                                     vizql_session=row[16],
                                     site_id=row[17],
                                     currentsheet=row[18])
            session.merge(entry)

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
