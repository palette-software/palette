import time
from datetime import datetime

from sqlalchemy import Column, BigInteger, Integer, String, DateTime
from sqlalchemy.schema import ForeignKey
from sqlalchemy.orm.exc import NoResultFound

from akiri.framework.ext.sqlalchemy import meta

from event_control import EventControl
from profile import UserProfile
from mixin import BaseDictMixin
from util import utc2local, DATEFMT

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
    system_users_id = Column(Integer)


class ExtractManager(object):

    def __init__(self, server):
        self.server = server

    def load(self, agent):
        stmt = "SELECT background_jobs.id, finish_code, notes, " +\
            "started_at, completed_at, title, subtitle, " +\
            "background_jobs.site_id, owner_id " +\
            "FROM background_jobs LEFT OUTER JOIN workbooks " +\
            "ON background_jobs.title = workbooks.name " +\
            "WHERE job_name = 'Refresh Extracts' AND progress = 100"

        session = meta.Session()

        lastid = self.get_lastid()
        if not lastid is None:
            stmt += " AND background_jobs.id > " + lastid

        stmt += " ORDER BY background_jobs.id ASC"

        data = agent.odbc.execute(stmt)

        if 'error' in data or '' not in data:
            return data

        FMT = "%Y-%m-%d %H:%M:%SZ"
        for row in data['']:
            started_at = utc2local(datetime.strptime(row[3], FMT))
            completed_at = utc2local(datetime.strptime(row[4], FMT))
            entry = ExtractEntry(extractid=row[0],
                                 agentid=agent.agentid,
                                 finish_code=row[1],
                                 notes=row[2],
                                 started_at=started_at,
                                 completed_at=completed_at,
                                 title=row[5],
                                 subtitle=row[6],
                                 site_id=row[7],
                                 system_users_id=row[8])

            body = dict(agent.__dict__.items() + entry.todict().items())
            if entry.finish_code == 0:
                self.eventgen(EventControl.EXTRACT_OK, body,
                              row[8], row[7],
                              timestamp=completed_at.strftime(DATEFMT))
            else:
                self.eventgen(EventControl.EXTRACT_FAILED, body,
                              row[8], row[7],
                              timestamp=completed_at.strftime(DATEFMT))

            session.add(entry)

        session.commit()

        return {u'status': 'OK',
                u'count': len(data[''])}

    def get_lastid(self):
        entry = meta.Session.query(ExtractEntry).\
            order_by(ExtractEntry.extractid.desc()).first()
        if entry:
                return str(entry.extractid)
        return None

    def eventgen(self, key, data, userid, siteid, timestamp=None):
        return self.server.event_control.gen(key, data, userid=userid,
                                                        siteid=siteid,
                                                        timestamp=timestamp)

    @classmethod
    def publishers(cls):
        query = meta.Session.query(UserProfile).\
            join(ExtractEntry,
                 UserProfile.system_users_id == ExtractEntry.system_users_id)
        return query.all()
