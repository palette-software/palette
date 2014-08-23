from sqlalchemy import Column, Integer, BigInteger, String, DateTime, func
from sqlalchemy import ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound

from akiri.framework.ext.sqlalchemy import meta

from agent import Agent
from agentinfo import AgentVolumesEntry
from agentmanager import AgentManager

from manager import Manager
from util import DATEFMT

class BackupEntry(meta.Base):
    __tablename__ = 'backup'

    backupid = Column(Integer, unique=True, nullable=False, primary_key=True)
    envid = Column(BigInteger, ForeignKey("environment.envid"))
    name = Column(String)
    gcsid = Column(BigInteger, ForeignKey("gcs.gcsid"))
    s3id = Column(BigInteger, ForeignKey("s3.s3id"))
    agentid = Column(BigInteger, ForeignKey("agent.agentid"))
    auto = Column(Boolean)  # automatically requested/scheduled
    encrypted = Column(Boolean)  # whether or not it is encrypted
    creation_time = Column(DateTime, server_default=func.now())
    modification_time = Column(DateTime, server_default=func.now(), \
                               server_onupdate=func.current_timestamp())
    UniqueConstraint('envid', 'name')

    # FIXME: make this a mixin
    def todict(self, pretty=False):
        d = { 'gcsid': self.gcsid,
              's3id': self.s3id,
              'agentid': self.agentid,
              'name': self.name}
        if pretty:
            d['creation-time'] = self.creation_time.strftime(DATEFMT)
            d['modification-time'] = self.modification_time.strftime(DATEFMT)
        else:
            d['creation_time'] = str(self.creation_time)
            d['modification_time'] = str(self.modification_time)
        return d


class BackupManager(Manager):

    def add(self, name, gcsid=None, s3id=None, agentid=None):
        session = meta.Session()
        entry = BackupEntry(name=name, envid=self.envid,
                            gcsid=gcsid, s3id=s3id, agentid=agentid)
        session.add(entry)
        session.commit()

    def remove(self, backupid):
        session = meta.Session()
        session.query(BackupEntry).\
            filter(BackupEntry.envid == self.envid).\
            filter(BackupEntry.backupid == backupid).\
            delete()
        session.commit()

    def find_by_name(self, name):
        try:
            return meta.Session.query(BackupEntry).\
                filter(BackupEntry.envid == self.envid).\
                filter(BackupEntry.name == name).\
                one()

        except NoResultFound, e:
            return None

    @classmethod
    def find_by_name_envid(cls, name, envid):
        try:
            return meta.Session.query(BackupEntry).\
                filter(BackupEntry.name == name).\
                filter(BackupEntry.envid == envid).\
                one()

        except NoResultFound, e:
            return None

    def get_palette_primary_data_loc_vol_entry(self, primary_agent):
        """
            Must pass in the primary agent.
            (We could look it up, but so need to be called only
            when we have a primary agent.)
        """
        # fixme: also support linux agent

        if primary_agent.agent_type != AgentManager.AGENT_TYPE_PRIMARY:
            # fixme: log this?
            return None

        palette_primary_data_dir = primary_agent.data_dir
        palette_primary_data_vol = palette_primary_data_dir.split(':')[0]

        try:
            return meta.Session.query(AgentVolumesEntry).\
                filter(AgentVolumesEntry.agentid == primary_agent.agentid).\
                filter(AgentVolumesEntry.name == palette_primary_data_vol).\
                one()
        except NoResultFound:
            return None

    def palette_primary_data_loc_path(self, agent):
        """
            Must pass in the primary agent.
        """
        return agent.data_dir

    @classmethod
    def is_pal_pri_data_vol(cls, agent, name):
        """
            Arguments:
                name:       volume (windows) or directory (linux) name
            Returns:
                 True if name is the palette primary data volume.
                 False if not.
        """
        if agent.agent_type != AgentManager.AGENT_TYPE_PRIMARY:
            return False

        # fixme: support linux too
        palette_primary_data_vol = agent.data_dir.split(':')[0]
        if name == palette_primary_data_vol:
            return True
        else:
            return False

    @classmethod
    def all(cls, envid, asc=True):
        """
        fixme: finish this.
        sql = \
            "SELECT backup agent_volumes FROM backup, agent_volumes " + \
            "WHERE backup.agentid = agent_volumes.agentid AND " + \
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
