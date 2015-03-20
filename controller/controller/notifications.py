from sqlalchemy import Column, BigInteger, DateTime, String, func
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.schema import ForeignKey

import akiri.framework.sqlalchemy as meta

class NotificationEntry(meta.Base):
    # pylint: disable=no-init
    __tablename__ = "notifications"

    notificationid = Column(BigInteger, unique=True, nullable=False,
                             autoincrement=True, primary_key=True)

    envid = Column(BigInteger, ForeignKey("environment.envid"))
    name = Column(String)   # 'cpu', 'memory', etc.
    agentid = Column(BigInteger,
                     ForeignKey("agent.agentid", ondelete='CASCADE'),
                     nullable=True)

    color = Column(String)
    notified_color = Column(String)
    description = Column(String)    # reason or metric for the notification
    creation_time = Column(DateTime, server_default=func.now())
    modification_time = Column(DateTime, server_default=func.now(),
                                     server_onupdate=func.current_timestamp())

class NotificationManager(object):

    def __init__(self, server):
        self.server = server
        self.log = server.log
        self.envid = server.environment.envid

    def get(self, name, agentid=None):
        query = meta.Session.query(NotificationEntry).\
            filter(NotificationEntry.envid == self.envid).\
            filter(NotificationEntry.name == name)

        if agentid:
            query = query.filter(NotificationEntry.agentid == agentid)

        try:
            entry = query.one()
        except NoResultFound:
            entry = NotificationEntry(envid=self.envid, name=name)
            if agentid:
                entry.agentid = agentid
            meta.Session.add(entry)
        return entry

    @classmethod
    def get_entry_by_envid_name_agentid(cls, envid, name, agentid):
        try:
            entry = meta.Session.query(NotificationEntry).\
                filter(NotificationEntry.envid == envid).\
                filter(NotificationEntry.name == name).\
                filter(NotificationEntry.agentid == agentid).\
                one()
        except NoResultFound:
            return None
        return entry
