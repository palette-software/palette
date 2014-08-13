from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Boolean
from sqlalchemy import func
from sqlalchemy.schema import ForeignKey, UniqueConstraint
from sqlalchemy.orm import reconstructor
from sqlalchemy.orm.exc import NoResultFound

from akiri.framework.ext.sqlalchemy import meta
from mixin import BaseDictMixin

from agentinfo import AgentVolumesEntry
from util import sizestr

import ntpath
import posixpath

class Agent(meta.Base, BaseDictMixin):
    __tablename__ = 'agent'

    agentid = Column(BigInteger, unique=True, nullable=False, \
                         autoincrement=True, primary_key=True)
    envid = Column(BigInteger, ForeignKey("environment.envid"))
    uuid = Column(String, unique=True, index=True)
    displayname = Column(String)
    display_order = Column(Integer)
    enabled = Column(Boolean, default=True, nullable=False)
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
    bitness = Column(Integer)
    install_dir = Column(String, nullable=False)
    data_dir = Column(String)
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
        self.filemanager = None

    def __getattr__(self, name):
        if name == 'iswin':
            if 'microsoft' in self.os_version.lower():
                return True
            else:
                return False
        if name == 'path':
            if 'microsoft' in self.os_version.lower():
                return ntpath
            else:
                return posixpath
        raise AttributeError(name)

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
        del d['username']
        del d['password']
        if pretty:
            fmt = "%(value).0f%(symbol)s"
            d['installed-memory-readable'] = \
                sizestr(self.installed_memory, fmt=fmt)
        return d        

    @classmethod
    def build(cls, envid, aconn):
         """Create an agent from a new connection."""
         body = aconn.auth
         session = meta.Session()

         uuid = body['uuid']
         entry = Agent.get_by_uuid(envid, uuid)

         if entry is None:
             entry = Agent(envid=envid, uuid=uuid)

         entry.version=body['version']
         entry.os_version=body['os-version']
         entry.processor_type=body['processor-type']
         entry.processor_count=body['processor-count']
         entry.installed_memory=body['installed-memory']
         entry.hostname=body['hostname']
         entry.fqdn=body['fqdn']
         entry.ip_address=body['ip-address']
         entry.listen_port=body['listen-port']
         entry.agent_type=aconn.agent_type
         entry.username=u'palette'# fixme
         entry.password=u'tableau2014'

         entry.install_dir=body['install-dir']


         # FIXME: make required when all agents are updated.
         if 'os-bitness' in body:
             entry.bitness = body['os-bitness']

         entry.last_connection_time = func.now()
         entry = session.merge(entry)
         session.commit()

         if entry.iswin:
             entry.path = ntpath
             parts = body['data-dir'].split(':')
             entry.data_dir = ntpath.join(parts[0].upper() + ':',
                                          parts[1])
         else:
             entry.path = posixpath
             entry.data_dir=body['data-dir']

         return entry
