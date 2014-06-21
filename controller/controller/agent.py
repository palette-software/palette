from sqlalchemy import Column, Integer, BigInteger, String, DateTime, func
from sqlalchemy.schema import ForeignKey, UniqueConstraint
from sqlalchemy.orm import reconstructor
from sqlalchemy.orm.exc import NoResultFound

from akiri.framework.ext.sqlalchemy import meta
from mixin import BaseDictMixin

from agentinfo import AgentVolumesEntry
from util import sizestr

class Agent(meta.Base, BaseDictMixin):
    __tablename__ = 'agent'

    agentid = Column(BigInteger, unique=True, nullable=False, \
                         autoincrement=True, primary_key=True)
    envid = Column(BigInteger, ForeignKey("environment.envid"))
    uuid = Column(String, unique=True, index=True)
    displayname = Column(String)
    display_order = Column(Integer)
    hostname = Column(String)
    fqdn = Column(String)
    agent_type = Column(String)
    version = Column(String)
    ip_address = Column(String)
    listen_port = Column(Integer)
    username = Column(String)
    password = Column(String)
    os_version = Column(String)
    installed_memory = Column(BigInteger)
    processor_type = Column(String)
    processor_count = Column(Integer)
    tableau_install_dir = Column(String)
    tableau_data_dir = Column(String)
    tableau_data_size = Column(BigInteger)
    creation_time = Column(DateTime, server_default=func.now())
    modification_time = Column(DateTime, server_default=func.now(), \
                                   server_onupdate=func.current_timestamp())
    last_connection_time = Column(DateTime, server_default=func.now())
    last_disconnect_time = Column(DateTime)
    UniqueConstraint('envid', 'displayname')

    def __init__(self, *args, **kwargs):
        super(Agent, self).__init__(*args, **kwargs)
        self.reconstruct()

    @reconstructor
    def reconstruct(self):
        self.server = None
        self.connection = None
        self.odbc = None
        self.firewall = None

    def connected(self):
        if not self.last_disconnect_time or \
                        self.last_disconnect_time < self.last_connection_time:
            return True # connected
        else:
            return False # not connected

    @classmethod
    def get_by_id(cls, agentid):
        try:
            entry = meta.Session.query(Agent).\
                filter(Agent.agentid == agentid).one()
        except NoResultFound:
            return None
        return entry

    @classmethod
    def get_by_uuid(cls, envid, uuid):
        try:
            entry = meta.Session.query(Agent).\
                filter(Agent.envid == envid).\
                filter(Agent.uuid == uuid).one()
        except NoResultFound:
            return None
        return entry

    @classmethod
    def display_order_by_envid(cls, envid):
        """Returns a list of agent uuids, sorted by display_order."""
        agent_entries = meta.Session.query(Agent).\
            filter(Agent.envid == envid).\
            order_by(Agent.display_order).\
            all()

        agents_sorted = [entry.uuid for entry in agent_entries]
        return agents_sorted

    @classmethod
    def get_agentstatusentry_by_volid(cls, volid):
        vol_entry = AgentVolumesEntry.get_vol_entry_by_volid(volid)
        if not vol_entry:
            return False

        return meta.Session.query(Agent).\
            filter(Agent.agentid == vol_entry.agentid).\
            one()

    def todict(self, pretty=False, exclude=[]):
        d = super(Agent, self).todict(pretty=pretty, exclude=exclude)
        if pretty:
            fmt = "%(value).0f%(symbol)s"
            d['installed-memory-readable'] = \
                sizestr(self.installed_memory, fmt=fmt)
        return d
