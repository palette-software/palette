import ntpath

from sqlalchemy import Column, Integer, BigInteger, String, DateTime, func
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound

from akiri.framework.ext.sqlalchemy import meta

from agent import Agent
from agentinfo import AgentVolumesEntry

class BackupEntry(meta.Base):
    __tablename__ = 'backup'
    DATEFMT = "%I:%M %p PDT on %B %d, %Y"

    backupid = Column(Integer, unique=True, nullable=False, primary_key=True)
    volid = Column(BigInteger, ForeignKey("agent_volumes.volid"))
    name = Column(String)
    creation_time = Column(DateTime, server_default=func.now())
    modification_time = Column(DateTime, server_default=func.now(), \
      server_onupdate=func.current_timestamp())
    UniqueConstraint('volid', 'name')

    # FIXME: make this a mixin
    def todict(self, pretty=False):
        d = {'volid': self.volid,
             'name': self.name}
        if pretty:
            d['creation-time'] = self.creation_time.strftime(self.DATEFMT)
            d['modification-time'] = self.modification_time.strftime(self.DATEFMT)
        else:
            d['creation_time'] = str(self.creation_time)
            d['modification_time'] = str(self.modification_time)
        return d


class BackupManager(object):

    def __init__(self, envid):
        self.envid = envid

    def add(self, name, volid):
        session = meta.Session()
        entry = BackupEntry(name=name, volid=volid)
        session.add(entry)
        session.commit()

    def remove(self, backupid):
        session = meta.Session()
        session.query(BackupEntry).\
            filter(BackupEntry.backupid == backupid).\
            delete()
        session.commit()

    def find_by_name(self, name):
        sql = \
            ("SELECT backup.backupid, agent_volumes.volid, " + \
            "agent_volumes.name, agent_volumes.path, " + \
            "agent_volumes.agentid FROM " + \
                                            "agent_volumes, backup WHERE " + \
            "backup.volid = agent_volumes.volid " + \
            "AND backup.name = '%s' AND " + \
            "agent_volumes.volid in " + \
            "(SELECT agent.agentid FROM agent WHERE agent.envid = %d)") % \
            (name, self.envid)

        result = meta.Session.execute(sql).fetchall()
        return result

    def get_primary_data_loc_vol_entry(self):
        try:
            vol_entry, agent_status_entry = \
                meta.Session.query(AgentVolumesEntry, Agent).\
                filter(AgentVolumesEntry.primary_data_loc == True).\
                filter(AgentVolumesEntry.agentid == Agent.agentid).\
                filter(Agent.envid == self.envid).\
                one()

            return vol_entry

        except NoResultFound, e:
            return None

    def primary_data_loc_path(self):
        vol_entry = self.get_primary_data_loc_vol_entry()

        if not vol_entry:
            return None

        return ntpath.join(vol_entry.name + ':', vol_entry.path)

    @classmethod
    def all(cls, envid, asc=True):
        """
        fixme: finish this.
        sql = \
            "SELECT backup agent_volumes FROM backup, agent_volumes " + \
            "WHERE backup.volid = agent_volumes.volid AND " + \
            "agent_volumes.agentid IN " + \
            "(SELECT agent.agentid FROM agent WHERE agent.envid = %d) " + \
            "ORDER BY backup.creation_time " % (envid)

        if asc:
            sql += "ASC"
        else:
            sql += "DESC"

        return meta.engine.execute(sql)
        """

        q = meta.Session.query(BackupEntry)
        if asc:
            q = q.order_by(BackupEntry.creation_time.asc())
        else:
            q = q.order_by(BackupEntry.creation_time.desc())
        return q.all()
