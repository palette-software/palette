import os
import ntpath
import posixpath

from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Boolean
from sqlalchemy import func, asc
from sqlalchemy.schema import ForeignKey, UniqueConstraint
from sqlalchemy.orm import reconstructor, relationship, backref
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

# pylint: disable=import-error,no-name-in-module
from akiri.framework.ext.sqlalchemy import meta
# pylint: enable=import-error,no-name-in-module

from mixin import BaseDictMixin
from util import sizestr, is_ip, hostname_only

class Agent(meta.Base, BaseDictMixin):
    # pylint: disable=too-many-instance-attributes
    __tablename__ = 'agent'

    agentid = Column(BigInteger, unique=True, nullable=False,
                         autoincrement=True, primary_key=True)
    conn_id = Column(BigInteger)
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
    peername = Column(String)
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
        self.path = None
        self.connection = None # fixes an erroneous pylint error.

    @reconstructor
    def reconstruct(self):
        # pylint: disable=attribute-defined-outside-init
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
    def get_agentid_from_host(cls, envid, host, enabled_agents_only=True):
        """ Given a hostname, fully qualified domain name or IP address,
            return an agentid.  If no agentid is found, return None.
            Hostname is treated as case insensitive.
            Note: Only enabled agents are checked."""

        session = meta.Session()
        query = session.query(Agent).\
            filter(Agent.envid == envid)

        if is_ip(host):
            query = query.filter(Agent.ip_address == host)
            if enabled_agents_only:
                query = query.filter(Agent.enabled == True)
            try:
                entry = query.one()
                return entry.agentid
            except NoResultFound:
                return None
            except MultipleResultsFound:
                # FIXME: log error
                pass
            return None

        hostname = hostname_only(host).upper()

        query = query.filter(func.upper(Agent.hostname) == hostname)
        if enabled_agents_only:
            query = query.filter(Agent.enabled == True)
        try:
            entry = query.one()
            return entry.agentid
        except NoResultFound:
            return None
        except MultipleResultsFound:
            # FIXME: log error
            return None

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

    def todict(self, pretty=False, exclude=None):
        if exclude is None:
            exclude = []
        d = super(Agent, self).todict(pretty=pretty, exclude=exclude)
        if not 'displayname' in d:
            # We may need the displayname to exist for events, even
            # before the agent has a displayname.
            if 'hostname' in d:
                d['displayname'] = d['hostname']
            else:
                d['displayname'] = d['uuid']
        if 'username' in d:
            del d['username']
        if 'password' in d:
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
        if entry:
            # Make a copy of the object
            entry = session.merge(entry)
            # but points at the same aconn...
        else:
            entry = Agent(envid=envid, uuid=uuid)
            session.add(entry)

        entry.conn_id = aconn.conn_id
        entry.version = body['version']
        entry.os_version = body['os-version']
        entry.processor_type = body['processor-type']
        entry.processor_count = body['processor-count']
        entry.installed_memory = body['installed-memory']
        entry.hostname = body['hostname']
        entry.fqdn = body['fqdn']
        entry.ip_address = body['ip-address']
        entry.peername = aconn.peername
        entry.listen_port = body['listen-port']

        # Note: Do not set agent_type here since 1) We need to know
        # what the agent_type was in the case where the row existed, and
        # 2) the agent_type isn't known yet at the time we are called anyway.
        entry.username = u'palette'# fixme
        entry.password = u'tableau2014'

        entry.install_dir = body['install-dir']

        # FIXME: make required when all agents are updated.
        if 'os-bitness' in body:
            entry.bitness = body['os-bitness']

        entry.last_connection_time = func.now()
        session.commit()

        if entry.iswin:
            entry.path = ntpath
            parts = body['data-dir'].split(':')
            entry.data_dir = ntpath.join(parts[0].upper() + ':', parts[1])
        else:
            entry.path = posixpath
            entry.data_dir = body['data-dir']
        return entry


class AgentVolumesEntry(meta.Base, BaseDictMixin):
    __tablename__ = "agent_volumes"

    volid = Column(Integer, unique=True, nullable=False, primary_key=True)

    agentid = Column(BigInteger, ForeignKey("agent.agentid"), nullable=False)

    name = Column(String)
    path = Column(String)
    vol_type = Column(String)
    label = Column(String)
    drive_format = Column(String)

    size = Column(BigInteger)
    available_space = Column(BigInteger)

    # Last notification about disk low or high watermark:
    #  "r" (red), "y" (yellow) or null.
    watermark_notified_color = Column(String(1))

    system = Column(Boolean)    # The OS/system is installed on this volume

    archive = Column(Boolean)
    archive_limit = Column(BigInteger)

    active = Column(Boolean)

    agent = relationship('Agent',
                         backref=backref('volumes',
                                         order_by='AgentVolumesEntry.name')
                         )
    UniqueConstraint('agentid', 'name')

    def todict(self, pretty=False, exclude=None):
        d = super(AgentVolumesEntry, self).todict(pretty=pretty)
        if not self.size is None and not self.available_space is None:
            d['used'] = self.size - self.available_space
        if not pretty:
            return d
        if 'size' in d:
            d['size-readable'] = sizestr(d['size'])
        if 'available-space' in d:
            d['available-readable'] = sizestr(d['available-space'])
        if 'used' in d:
            d['used-readable'] = sizestr(d['used'])
        return d

    @classmethod
    def build(cls, agent, volume, install_data_dir):
        # pylint: disable=multiple-statements
        name = None; path = None; vol_type = None; label = None
        drive_format = None; archive = False; archive_limit = None
        size = None; available_space = None

        if volume.has_key("name"):
            name = volume['name']
            if agent.iswin:
                name = volume['name'].upper()

        if volume.has_key('path'):
            path = volume['path']

        if volume.has_key("size"):
            size = volume['size']

        if volume.has_key("type"):
            vol_type = volume['type']
            if agent.iswin and vol_type == 'Fixed':
                archive = True
                path = install_data_dir
            elif not agent.iswin and volume['type'][:7] == '/dev/sd' and \
                name != None and \
                        os.path.commonprefix([agent.data_dir, name]) == name:
                # The data-dir is on the entry's mount point so it is
                # the "archive" entry.
                archive = True
                path = install_data_dir

        if archive == True:
            if size:
                archive_limit = size    # fixme: can't use whole disk

        if volume.has_key("label"):
            label = volume['label']

        if volume.has_key("drive-format"):
            drive_format = volume['drive-format']

        if volume.has_key('available-space'):
            available_space = volume['available-space']

        return AgentVolumesEntry(agentid=agent.agentid, name=name, path=path,
            vol_type=vol_type, label=label, drive_format=drive_format,
            archive=archive, archive_limit=archive_limit, size=size,
            available_space=available_space, active=True)

    @classmethod
    def has_available_space(cls, agentid, min_needed):
        """Searches for a volume on the agent that has
        the requested disk space for archiving.  If found, returns
        the volume entry.  If not, returns False."""

        try:
            return meta.Session.query(AgentVolumesEntry).\
                    filter(AgentVolumesEntry.agentid == agentid).\
                    filter(AgentVolumesEntry.vol_type == "Fixed").\
                    filter(AgentVolumesEntry.archive == True).\
                    filter(AgentVolumesEntry.active == True).\
                    filter(AgentVolumesEntry.available_space >= min_needed).\
                    filter(AgentVolumesEntry.size - \
                                AgentVolumesEntry.available_space +
                                min_needed < AgentVolumesEntry.archive_limit).\
                    one()   # for now, choosen any one - no particular order.

        except NoResultFound:
            return False

    @classmethod
    def get_vol_entry_by_agentid_vol_name(cls, agentid, vol_name):
        # pylint: disable=invalid-name
        try:
            return meta.Session.query(AgentVolumesEntry).\
                filter(AgentVolumesEntry.agentid == agentid).\
                filter(AgentVolumesEntry.name == vol_name).\
                one()
        except NoResultFound:
            return None

    @classmethod
    def get_vol_entry_by_volid(cls, volid):
        # pylint: disable=invalid-name
        try:
            return meta.Session.query(AgentVolumesEntry).\
                filter(AgentVolumesEntry.volid == volid).\
                one()
        except NoResultFound:
            return None
    get_by_id = get_vol_entry_by_volid

    @classmethod
    def get_vol_entry_with_agent_by_volid(cls, volid):
        # pylint: disable=invalid-name
        try:
            return meta.Session.query(AgentVolumesEntry).\
                filter(AgentVolumesEntry.volid == volid).\
                join('agent').\
                filter_by(agentid=AgentVolumesEntry.agentid).\
                one()
        except NoResultFound:
            return None

    @classmethod
    def get_vol_archive_entries_by_agentid(cls, agentid):
        # pylint: disable=invalid-name
        return meta.Session.query(AgentVolumesEntry).\
            filter(AgentVolumesEntry.archive == True).\
            filter(AgentVolumesEntry.agentid == agentid).\
            order_by(AgentVolumesEntry.name.desc()).\
            all()

    @classmethod
    def get_archives_by_envid(cls, envid, enabled_agents_only=True):
        query = meta.Session.query(AgentVolumesEntry).\
            filter_by(archive=True).\
            join('agent').\
            filter_by(envid=envid)

        if enabled_agents_only:
            query = query.filter_by(enabled=True)

        return query.order_by(asc('agent.display_order'), asc('name')).\
            all()
