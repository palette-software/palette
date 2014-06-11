import sys
import os
import socket
import ssl
import select
import threading
import time
import traceback
from httplib import HTTPConnection
import json
import ntpath

import exc
import httplib

from agent import Agent
from agentinfo import AgentYmlEntry, AgentVolumesEntry
from state import StateManager
from event_control import EventControl
from filemanager import FileManager
from firewall import Firewall
from odbc import ODBC

from sqlalchemy import func, or_
from sqlalchemy.orm.exc import NoResultFound
from akiri.framework.ext.sqlalchemy import meta

# The Controller's Agent Manager.
# Communicates with the Agent.
# fixme: maybe combine with the Agent class.
class AgentConnection(object):

    TABLEAU_DATA_DIR = ntpath.join("ProgramData", "Tableau", "Tableau Server")
    DATA_DIR = "Data"

    def __init__(self, server, conn, addr):
        self.server = server
        self.socket = conn
        self.addr = addr
        self.httpconn = False   # Used by the controller
        self.auth = {}          # Used by the controller
        self.agentid = None
        self.uuid = None
        self.displayname = None
        self.agent_type = None
        self.yml_contents = None    # only valid if agent is a primary
        self.initting = True

        # Each agent connection has its own lock to allow only
        # one thread to send/recv  on the agent socket at a time.
        self.lockobj = threading.RLock()

        # A lock for to allow only one user action (backup/restore/etc.)
        # at a time.
        self.user_action_lockobj = threading.Lock()

        self.filemanager = FileManager(self)
        self.odbc = ODBC(self)
        self.firewall = Firewall(self)

    def httpexc(self, res, method='GET', body=None):
        if body is None:
            body = res.read()
        raise exc.HTTPException(res.status, res.reason,
                                method=method, body=body)

    def http_send(self, method, uri, body=None):
        # Check to see if state is not PENDING or DISCONNECTED?
        self.lock()
        try:
            self.httpconn.request(method, uri, body)
            res = self.httpconn.getresponse()
            if res.status != httplib.OK:
                self.httpexc(res, method=method)
            return res.read()
        finally:
            self.unlock()

    def lock(self):
        self.lockobj.acquire()

    def unlock(self):
        self.lockobj.release()

    def user_action_lock(self, blocking=True):
        return self.user_action_lockobj.acquire(blocking)

    def user_action_unlock(self):
        self.user_action_lockobj.release()

class AgentManager(threading.Thread):

    PORT = 8888

    SSL_HANDSHAKE_TIMEOUT_DEFAULT = 5

    # Agent types
    AGENT_TYPE_PRIMARY="primary"
    AGENT_TYPE_WORKER="worker"
    AGENT_TYPE_ARCHIVE="archive"

    def __init__(self, server, host='0.0.0.0', port=0):
        super(AgentManager, self).__init__()
        self.server = server
        self.config = self.server.config
        self.log = self.server.log
        self.domainid = self.server.domain.domainid
        self.envid = self.server.environment.envid
        self.daemon = True
        self.lockobj = threading.RLock()
        self.new_primary_event = threading.Event() # a primary connected
        self.host = host
        self.port = port and port or self.PORT
        self.socket = None
        # A dictionary with all AgentConnections with the key being
        # the unique 'uuid'.
        self.agents = {}

        self.socket_timeout = self.config.getint('controller','socket_timeout', default=60)

        self.ssl = self.config.getboolean('controller','ssl', default=True)
        if self.ssl:
            self.ssl_handshake_timeout = self.config.getint('controller',
                'ssl_handshake_timeout',
                            default=AgentManager.SSL_HANDSHAKE_TIMEOUT_DEFAULT)
            if not self.config.has_option('controller', 'ssl_cert_file'):
                self.log.critical("Missing 'ssl_cert_file' certificate file specification")
                raise IOError("Missing 'ssl_cert_file' certificate file specification")
            self.cert_file = self.config.get('controller', 'ssl_cert_file')
            if not os.path.exists(self.cert_file):
                self.log.critical("ssl enabled, but ssl certificate file does not exist: %s", self.cert_file)
                raise IOError("Certificate file not found: " + self.cert_file)

    def update_last_disconnect_time(self):
        """Called during startup to set a disconnection time for agents that
           were still connected when we stopped."""

        session = meta.Session()

        session.query(Agent).\
            filter(or_(Agent.last_connection_time > \
                           Agent.last_disconnect_time, \
                           Agent.last_disconnect_time == None)).\
                           update({"last_disconnect_time" : func.now()}, \
                                      synchronize_session=False)
        session.commit()

    # must be called with the agentmanager lock held
    def find_by_uuid(self, uuid):
        for key in self.agents.keys():
            agent = self.agents[key]
            if agent.uuid == uuid:
                return agent
        return None

    def register(self, agent, body):
        """Called with the agent object and body /auth dictionary that
           was sent from the agent in json."""

        self.lock()
        self.log.debug("new agent: name %s, uuid %s", \
                           body['hostname'], body['uuid'])

        new_agent_type = agent.agent_type
        # Don't allow two primary agents to be connected and
        # don't allow two agents with the same name to be connected.
        # Keep the newest one.
        for key in self.agents:
            a = self.agents[key]
            if a.uuid == body['uuid']:
                self.log.info("Agent already connected with name '%s': " + \
                    "will remove it and use the new connection.", body['uuid'])
                self.remove_agent(a, ("An agent is already connected " + \
                    "named '%s': will remove it and use the new " + \
                        "connection.") % (body['uuid']), gen_event=False)
                break
            elif new_agent_type == AgentManager.AGENT_TYPE_PRIMARY and \
                        a.agent_type == AgentManager.AGENT_TYPE_PRIMARY:
                    self.log.info("A primary agent is already connected: " + \
                        "Will remove it and keep the new primary agent " + \
                        "connection.")
                    self.remove_agent(a,
                            "A primary agent is already connected: Will " + \
                            "remove it and keep the new primary agent " + \
                            "connection.", gen_event=False)

        if agent.displayname is None or agent.displayname == "":
            (displayname, display_order) = self.calc_new_displayname(agent.connection)
            agent.displayname = displayname
            agent.display_order = display_order

        self.agents[agent.uuid] = agent

        if new_agent_type == AgentManager.AGENT_TYPE_PRIMARY:
            self.log.debug("register: Initializing state entries on connect")
            stateman = StateManager(self.server)
            stateman.update(StateManager.STATE_PENDING)

            # Check to see if we need to reclassify archive agents as
            # worker agents.  For example, a worker may have
            # connected before the primary ever connected with its
            # yml file that tells us the ip addresses of workers.
            self.set_agent_types()

            # Tell the status thread to start getting status on
            # the new primary.
            self.new_primary_event.set()

        self.unlock()

        meta.Session.commit()
        return True

    def set_agent_types(self):
        """Look through the list of agents and reclassify archive agents as
        worker agents if needed.  For example, a worker may have
        connected and set as "archive" before the primary ever connected
        with its yml file that tells us the ip addresses of workers.
        """
        session = meta.Session()

        rows = session.query(Agent).\
            filter(Agent.agent_type != \
                                        AgentManager.AGENT_TYPE_PRIMARY).\
            all()

        for entry in rows:
            if self.is_tableau_worker(entry.ip_address):
                agent_type = AgentManager.AGENT_TYPE_WORKER
            else:
                agent_type = AgentManager.AGENT_TYPE_ARCHIVE

            if entry.agent_type != agent_type:
#                print "Correcting agent type from", entry.agent_type, "to", agent_type
                # Set the agent to the correct type.
                entry.agent_type = agent_type
                session.merge(entry)

        session.commit()

    def calc_new_displayname(self, new_agent):
        """
            Returns (agent-display-name, agent-display-order)
            The naming scheme for V1:
                Tableau Primary
                Tableau Worker #1
                Tableau Worker #2
                    ...
                Archive Server #1 (formerly "Other")
                Archive Server #2
                    ...
        """
        PRIMARY_TEMPLATE="Tableau Primary" # not a template since only 1
        WORKER_TEMPLATE="Tableau Worker #%d"
        ARCHIVE_TEMPLATE="Tableau Archive #%d"

        # Starting point for 
        WORKER_START=100
        ARCHIVE_START=200

        if new_agent.agent_type == AgentManager.AGENT_TYPE_PRIMARY:
            return (PRIMARY_TEMPLATE, 1)

        session = meta.Session()

        # Count how many of this agent type exist.
        rows = session.query(Agent).\
            filter(Agent.envid == self.envid).\
            filter(Agent.agent_type == new_agent.agent_type).\
            all()

        # The new agent will be the next one.
        count = len(rows) + 1

        if new_agent.agent_type == AgentManager.AGENT_TYPE_WORKER:
            return (WORKER_TEMPLATE % (count + WORKER_START), count + WORKER_START)
        elif new_agent.agent_type == AgentManager.AGENT_TYPE_ARCHIVE:
            return (ARCHIVE_TEMPLATE % (count + ARCHIVE_START),
                                                        count + ARCHIVE_START)
        self.log.error("calc_new_displayname: INVALID agent type: %s",
                                                            new_agent.agent_type)
        return ("INVALID AGENT TYPE: %s" % new_agent.agent_type, 0)

    # FIXME: get/create ?
    def remember(self, aconn, body):
        session = meta.Session()

        uuid = body['uuid']
        entry = Agent.get_by_uuid(self.envid, uuid)

        if entry is None:
            entry = Agent(envid=self.envid,
                          uuid=body['uuid'],
                          hostname=body['hostname'],
                          agent_type=aconn.agent_type,
                          version=body['version'],
                          ip_address=body['ip-address'],
                          listen_port=body['listen-port'],
                          username=u'palette',# fixme
                          password=u'tableau2014')

        entry.last_connection_time = func.now()
        entry = session.merge(entry)
        session.commit()
        return entry

    def update_agent_yml(self, agentid, yml):
        """update the agent_yml table with this agent's yml contents."""
        session = meta.Session()

        # FIXME: do an update instead of a delete all
        # First delete any old entries for this agent
        entry = session.query(AgentYmlEntry).\
            filter(AgentYmlEntry.agentid == agentid).delete()

        d = {}
        # This the first line ('---')
        for line in yml.strip().split('\n')[1:]:
            key, value = line.split(":", 1)
            value = value.strip()
            entry = AgentYmlEntry(agentid=agentid, key=key, value=value)
            session.add(entry)
            d[key] = value
        return d

    def update_agent_pinfo(self, agent, pinfo):
        agentid = agent.agentid

        session = meta.Session()
        # Set all of the agent volumes to 'inactive'.
        # Each volume pinfo sent us will later be set to 'active'.
        session.query(AgentVolumesEntry).\
            filter(AgentVolumesEntry.agentid == agentid).\
                   update({"active" : False}, synchronize_session=False)

        aconn = agent.connection
        parts = aconn.auth['install-dir'].split(':')
        if len(parts) != 2:
            self.log.error("Bad format for install-dir: %s",
                           aconn.auth['install-dir'])
            return False

        install_dir_vol_name = parts[0].upper()
        install_data_dir = ntpath.join(parts[1], AgentConnection.DATA_DIR)

        # FIXME: make automagic based on self.__table__.columns
        if 'fqdn' in pinfo:
            agent.fqdn = pinfo['fqdn']
        if 'os-version' in pinfo:
            agent.os_version = pinfo['os-version']
        if 'installed-memory' in pinfo:
            agent.installed_memory = pinfo['installed-memory']
        if 'processor-type' in pinfo:
            agent.processor_type = pinfo['processor-type']
        if 'processor-count' in pinfo:
            agent.processor_count = pinfo['processor-count']
        if 'tableau-install-dir' in pinfo:
            agent.tableau_install_dir = pinfo['tableau-install-dir']
        if 'tableau-data-dir' in pinfo:
            agent.tableau_data_dir = pinfo['tableau-data-dir']
        if 'tableau-data-size' in pinfo:
            agent.tableau_data_size = pinfo['tableau-data-size']

        if 'volumes' in pinfo:
            for volume in pinfo['volumes']:
                if 'name' in volume:
                    name = volume['name'].upper()
                else:
                    self.log.error("volume missing 'name' in pinfo for " + \
                        "agentid %d. Will ignore: %s", agentid, str(volume))
                    continue

                # Check to see if the volume alread exists.
                try:
                    entry = session.query(AgentVolumesEntry).\
                        filter(AgentVolumesEntry.agentid == agentid).\
                        filter(AgentVolumesEntry.name == name).\
                        one()
                    found = True
                except NoResultFound, e:
                    found = False

                if found:
                    # Merge it in to the existing volume entry.
                    # It should already have archive, archive_limit, etc.
                    if 'size' in volume:
                        entry.size = volume['size']
                    if 'label' in volume:
                        entry.label = volume['label']

                    if 'vol-type' in volume:
                        entry.vol_type = volume['vol_type']

                    if 'available-space' in volume:
                        entry.available_space = volume['available-space']

                    if 'drive-format' in volume:
                        entry.drive_format = volume['drive-format']

                    entry.active = True  # Note the agent reported it
                    session.merge(entry)
                else:
                    # Add the volume
                    if 'type' in volume:
                        if volume['type'] == "Fixed":
                            # Set a default path for new "Fixed" volumes.
                            # (Only "Fixed" volumes can be used for an archive.)
                            volume['path'] = install_data_dir

                        entry = AgentVolumesEntry.build(agentid, volume)

                        # If it is the primary agent and install volume,
                        # mark it as the "primary_data_loc" volume.
                        if aconn.agent_type == \
                                AgentManager.AGENT_TYPE_PRIMARY and \
                                install_dir_vol_name == name:
                            entry.primary_data_loc = True
                        else:
                            entry.primary_data_loc = False

                        session.add(entry)

        session.commit()

        # Sanity check.
        # If this is the primary agent, check to see if a volume
        # exists for the install directory.   There must be
        # one since 1) we use it for backups and 2) We need to
        # know how much available disk space is used on the backup
        # volume.
        if aconn.agent_type == AgentManager.AGENT_TYPE_PRIMARY and \
                not self.primary_data_vol_exists(agentid, install_dir_vol_name):
            self.log.error("pinfo for the primary did not include" + \
                               " the install dir volume.  " + \
                               "agentid: %d, install_dir_vol_name: %s",
                           agentid, install_dir_vol_name)
            return False

        return True

    def primary_data_vol_exists(self, agentid, install_dir_vol_name):
        """Check to see if there is a volume for the primary
           data directory.  If there is not one, add it.
           Return True if exists, False if doesn't exist.
        """
        try:
            entry = meta.Session.query(AgentVolumesEntry).\
                filter(AgentVolumesEntry.agentid == agentid).\
                filter(AgentVolumesEntry.name == install_dir_vol_name).\
                filter(AgentVolumesEntry.primary_data_loc == True).\
                one()
            return True
        except NoResultFound, e:
            return False

    def is_tableau_worker(self, ip):
        """Returns True if the passed ip adress (string) is
           known to be a tableau worker host.  The type of tableau host is
           reported in the tableau primary host's yml file on the
           "worker.hosts" line.  For example:
                worker.hosts:  DEV-PRIMARY, 10.0.0.102
            The first host is the primary, and subsequent hosts
            are the workers.
        """

        session = meta.Session()
        query = session.query(AgentYmlEntry).\
            filter(AgentYmlEntry.key == "worker.hosts").first()

        if not query:
            return False    # We don't know what it is until primary yml file

        # The value is in the format:
        #       "DEV-PRIMARY, 10.0.0.102"
        # where the first host is the primary and the remaining are
        # Tableau workers.
        hosts = [x.strip() for x in query.value.split(',')]
        if len(hosts) == 1:
            return False
        if ip in hosts:
            return True
        else:
            return False

    def set_displayname(self, aconn, uuid, displayname):
        session = meta.Session()
        try:
            entry = session.query(Agent).\
                filter(Agent.uuid == uuid).one()
            entry.displayname = displayname
            session.commit()
            if aconn:
                aconn.displayname = displayname
        except NoResultFound, e:
            raise ValueError('No agent found with uuid=%s' % (uuid))

    def forget(self, agentid):
        if not agentid:
            self.log.debug("forget:  Won't try to forget agentid of None")
            # Can happen if we sent a failed command to the agent
            # that hasn't been remembered yet.
            return

        session = meta.Session()
        #fixme: add try
        entry = session.query(Agent).\
            filter(Agent.agentid == agentid).\
            one()
        entry.last_disconnect_time = func.now()
        session.commit()

    # Return the list of all agents
    def all_agents(self):
        return self.agents

    def agent_connected(self, uuid):
        """Check to see if the passed agent is still connected.
        Returns:
            True if still conencted.
            False if not connected.
        """
        return uuid in self.agents

    def agent_conn_by_type(self, agent_type):
        """Returns an instance of a connected agent of the requested type,
        or a list of instances if more than one agent of that type
        is connected.

        Returns None if no agents of that type are connected."""

        for key in self.agents:
            if self.agents[key].agent_type == agent_type:
                return self.agents[key].connection

        return None

    def agent_conn_by_displayname(self, target):
        """Search for a connected agent with a displayname of the
        passed target.

        Return an instance of it, or None if none match."""

        for key in self.agents:
            if self.agents[key].displayname == target:
                return self.agents[key].connection

        return None

    def agent_conn_by_hostname(self, target):
        """Search for a connected agent with a hostname of the
        passed target.

        Return an instance of it, or None if none match."""

        for key in self.agents:
            if self.agents[key].connection.auth['hostname'] == target:
                return self.agents[key].connection

        return None

    def agent_by_uuid(self, uuid):
        """Search for agents with the given uuid.
            Return an instance of it, or None if none match.
        """
        for key in self.agents:
            if self.agents[key].uuid == uuid:
                return self.agents[key]
        return None

    # DEPRECATED
    def agent_conn_by_uuid(self, uuid):
        """Search for agents with the given uuid.
            Return an instance of it, or None if none match.
        """
        agent = self.agent_by_uuid(uuid)
        return agent and agent.connection or None

    def remove_agent(self, agent, reason="", gen_event=True):
        """Remove an agent.
            Args:
                agent:       The agent to remove.
                reason:      An optional message, describing why.
                gen_event:   True or False.  If True, generates an event.
                             If False does not generate an event.
        """
        if reason == "":
            reason = "Agent communication failure"

        self.lock()
        uuid = agent.uuid
        if self.agents.has_key(uuid):
            self.log.debug("Removing agent with uuid %s, name %s, reason: %s",\
                uuid, self.agents[uuid].connection.auth['hostname'], reason)

            if gen_event:
                self.server.event_control.gen(EventControl.AGENT_DISCONNECT,
                    dict({ 'error': reason,
                      'info': "\nAgent type: %s\nAgent uuid %s" %
                        (agent.displayname, uuid) }.items() +
                                            agent.__dict__.items()))

            self.forget(agent.agentid)
            self.log.debug("remove_agent: closing agent socket.")
            if self._close(agent.connection.socket):
                self.log.debug("remove_agent: close agent socket succeeded.")
            else:
                self.log.debug("remove_agent: close agent socket failed")

            del self.agents[uuid]
        else:
            self.log.debug("remove_agent: No such agent with uuid %s", uuid)
        if agent.agent_type == AgentManager.AGENT_TYPE_PRIMARY:
            self.log.debug("remove_agent: Initializing state entries on removal")
            stateman = StateManager(self.server)
            stateman.update(StateManager.STATE_DISCONNECTED)
            # Note: We don't update/clear the "reported" state from
            # a previous agent, so the user will see what was the last
            # real state.

        self.unlock()

    def _close(self, sock):
        try:
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
        except socket.error as e:
            self.log.debug("agentmanager._close socket failure: " + str(e))
            return False
        return True

    def lock(self):
        """Locks the agents list"""
        self.lockobj.acquire()

    def unlock(self):
        """Unlocks the agents list"""
        self.lockobj.release()

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM);
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))
        sock.listen(8)

        # Start socket monitor check thread
        asocketmon = AgentHealthMonitor(self, self.log)
        asocketmon.start()

        while True:
            try:
                conn, addr = sock.accept()
            except socket.error as e:
                self.log.debug("Accept failed.")
                continue

            tobj = threading.Thread(target=self.handle_agent_connection,
                                 args=(conn, addr))
            # Spawn a thread to handle the new agent connection
            tobj.start()

    def _shutdown(self, sock):
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except EnvironmentError:
            pass

    def socket_fd_closed(self, fd):
        """called with agentmanager lock"""
        for key in self.agents:
            agent = self.agents[key]
            self.log.debug("agent fileno to close: %d", agent.socket.fileno())
            if agent.connection.socket.fileno() == fd:
                self.log.debug("Agent closed connection for: %s", key)
                agent.socket.close()
                del self.agents[key]
                return

        self.log.error("Couldn't find agent with fd: %d", fd)

    # thread function: spawned on a new connection from an agent.
    def handle_agent_connection(self, conn, addr):
        if self.ssl:
            conn.settimeout(self.ssl_handshake_timeout)
            try:
                ssl_sock = ssl.wrap_socket(conn, server_side=True,
                                           certfile=self.cert_file)
                conn = ssl_sock
            except (ssl.SSLError, socket.error), e:
                self.log.info("Exception with ssl wrap: %s", str(e))
                # http://bugs.python.org/issue9211, though takes
                # a while to garbage collect and close the fd.
                self._shutdown(conn)
                return

        self.log.debug("New socket accepted.")
        conn.settimeout(self.socket_timeout)

        try:
            aconn = AgentConnection(self.server, conn, addr)

            # sleep for 100ms to prevent:
            #  'An existing connection was forcibly closed by the remote host'
            # on the Windows client when the agent tries to connect.
            time.sleep(.1);

            aconn.httpconn = ReverseHTTPConnection(conn)
            # FIXME: why is this a POST?
            body_json = aconn.http_send('POST', '/auth')
            if body_json:
                body = json.loads(body_json)
                self.log.debug("body = " + str(body))
            else:
                body = {}
                self.log.debug("done.")

            # Inspect the reply to make sure it has all the required values.
            required = ['hostname', 'ip-address', \
                            'version', 'listen-port', 'uuid', 'install-dir']
            for item in required:
                if not body.has_key(item):
                    self.log.error("Missing '%s' from agent" % item)
                    self._close(conn)
                    return

            aconn.auth = body
            uuid = aconn.auth['uuid']

            agent = self.remember(aconn, body)
            agent.connection = aconn
            aconn.agentid = agent.agentid
            aconn.uuid = uuid

            if not self.server.init_new_agent(agent):
                self.log.error("Bad agent.  Disconnecting.")
                self._close(conn)
                return

            if agent.agent_type is None:
                agent.agent_type = aconn.agent_type

            if not self.register(agent, body):
                self.log.error("Bad agent.  Disconnecting.")
                self._close(conn)
                return

            self.save_routes(aconn) # fixme: check return value?
            aconn.initting = False

        except socket.error, e:
            self.log.debug("Socket error: " + str(e))
            self._close(conn)
        except Exception, e:
            self.log.error("Exception:")
            traceback.format_exc()
            self.log.error(str(e))
            self.log.error(traceback.format_exc())

    def save_routes(self, aconn):
        lines = ""
        rows = meta.Session().query(AgentVolumesEntry).\
            filter(AgentVolumesEntry.agentid == aconn.agentid).\
            all()

        lines = []
        for volentry in rows:
            if not volentry.archive:
                continue
            lines.append("%s:%s\r\n" % (volentry.name, volentry.path))

        # remove duplicate lines: The primary_data_loc could be
        # the same as a volume path entered by the user.
        lines = list(set(lines))

        lines = ''.join(lines)

        if 'install-dir' not in aconn.auth:
            self.log.error("save_routes: agent is missing 'install-dir'")
            return

        route_path = ntpath.join(aconn.auth['install-dir'], "conf", "archive",
                                                                "routes.txt")
        try:
            aconn.filemanager.put(route_path, lines)
        except (exc.HTTPException, httplib.HTTPException,
                                                    EnvironmentError) as e:
            self.log.error(\
                "filemanager.put(%s) on %s failed with: %s",
                                    aconn.displayname, route_path, str(e))
            return False

        self.log.debug("Saved agent file '%s' with contents: %s",
                                                    route_path, lines)
        return True

class ReverseHTTPConnection(HTTPConnection):

    def __init__(self, sock):
        HTTPConnection.__init__(self, 'agent')
#        HTTPConnection.debuglevel = 1
        self.sock = sock

    def connect(self):
        pass

    def close(self):
        pass

class AgentHealthMonitor(threading.Thread):

    def __init__(self, manager, log):
        super(AgentHealthMonitor, self).__init__()
        self.manager = manager
        self.server = manager.server
        self.log = log
        self.config = self.manager.config
        self.ping_interval = self.config.getint('status', 'ping_request_interval', default=10)

    def run(self):

        self.log.debug("Starting agent health monitor.")

        while True:
            if len(self.manager.agents) == 0:
                # no agents to check on
                # self.log.debug("no agents to ping")
                time.sleep(self.ping_interval)
                continue

            agents = self.manager.all_agents()
            self.log.debug("about to ping %d agent(s)", len(agents))
            for key in agents.keys():
                self.manager.lock()

                if not agents.has_key(key):
                    self.log.debug("agent with uuid '%s' is now gone and won't be checked." %
                        key)
                    self.manager.unlock()
                    continue
                agent = agents[key]
                self.manager.unlock()

                self.log.debug("Ping: check for agent '%s', type '%s', uuid %s." % \
                        (agent.displayname, agent.agent_type, key))

                # fixme: add a timeout ?
                body = self.server.ping(agent.connection)
                if body.has_key('error'):
                    self.log.info("Ping: Agent '%s', type '%s', uuid %s did not respond to ping.  Removing." %
                        (agent.displayname, agent.agent_type, key))

                    self.manager.remove_agent(agent, "Lost contact with an agent")
                else:
                    self.log.debug("Ping: Reply from agent '%s', type '%s', uuid %s." %
                        (agent.displayname, agent.agent_type, key))

            time.sleep(self.ping_interval)
