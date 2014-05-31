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

from agentstatus import AgentStatusEntry
from agentinfo import AgentYmlEntry, AgentInfoEntry, AgentVolumesEntry
from state import StateManager
from alert import Alert
from custom_alerts import CustomAlerts
from filemanager import FileManager
from firewall import Firewall
from odbc import ODBC

from sqlalchemy import func, or_
from sqlalchemy.orm.exc import NoResultFound
from akiri.framework.ext.sqlalchemy import meta

# The Controller's Agent Manager.
# Communicates with the Agent.
# fixme: maybe combine with the AgentStatusEntry class.
class AgentConnection(object):

    TABLEAU_DATA_DIR = ntpath.join("ProgramData", "Tableau", "Tableau Server")
    DEFAULT_VOLUME_PATH = ntpath.join("\\", "Program Files (x86)", "Palette",
                                                                        "Data")
    DATA_DIR = "Data"

    def __init__(self, server, conn, addr):
        self.server = server
        self.socket = conn
        self.addr = addr
        self.httpconn = False   # Used by the controller
        self.auth = {}          # Used by the controller
        self.agentid = None
        self.uuid = None
        self.tableau_install_dir = None
        self.agent_type = None
        self.yml_contents = None    # only valid if agent is a primary
        self.pinfo = {}  # from pinfo
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

    def get_tableau_data_dir(self):
        if not self.tableau_install_dir:
            return None
        volume = self.tableau_install_dir.split(':')[0]
        return ntpath.join(volume + ':\\', AgentConnection.TABLEAU_DATA_DIR)

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
        self.domainid = self.server.domainid
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

        session.query(AgentStatusEntry).\
            filter(or_(AgentStatusEntry.last_connection_time > \
                           AgentStatusEntry.last_disconnect_time, \
                           AgentStatusEntry.last_disconnect_time == None)).\
                           update({"last_disconnect_time" : func.now()}, \
                                      synchronize_session=False)
        session.commit()

    def register(self, new_agent, body):
        """Called with the agent object and body /auth dictionary that
           was sent from the agent in json."""

        # The agent initialization succeeded.
        new_agent.initting = False

        self.lock()
        self.log.debug("new agent: name %s, uuid %s", \
          body['hostname'], body['uuid'])

        new_agent_type = new_agent.agent_type
        # Don't allow two primary agents to be connected and
        # don't allow two agents with the same name to be connected.
        # Keep the newest one.
        for key in self.agents.keys():
            agent = self.agents[key]
            if agent.uuid == body['uuid']:
                self.log.info("Agent already connected with name '%s': will remove it and use the new connection.", body['uuid'])
                self.remove_agent(agent, "An agent is already connected named '%s': will remove it and use the new connection." % body['uuid'], send_alert=False)
                break
            elif new_agent_type == AgentManager.AGENT_TYPE_PRIMARY and \
                        agent.agent_type == AgentManager.AGENT_TYPE_PRIMARY:
                    self.log.info("A primary agent is already connected: will remove it and keep the new primary agent connection.")
                    self.remove_agent(agent, "A primary agent is already connected: will remove it and keep the new primary agent connection.", send_alert=False)

        # Remember the new agent
        entry = self.remember(new_agent, body)
        if entry:
            new_agent.agentid = entry.agentid
            new_agent.uuid = entry.uuid
            new_agent.displayname = entry.displayname
        else:
            # FIXME: handle this as an error
            pass
        self.agents[new_agent.uuid] = new_agent

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

    def set_agent_types(self):
        """Look through the list of agents and reclassify archive agents as
        worker agents if needed.  For example, a worker may have
        connected and set as "archive" before the primary ever connected
        with its yml file that tells us the ip addresses of workers.
        """
        session = meta.Session()

        rows = session.query(AgentStatusEntry).\
            filter(AgentStatusEntry.agent_type != \
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
        rows = session.query(AgentStatusEntry).\
            filter(AgentStatusEntry.domainid == self.domainid).\
            filter(AgentStatusEntry.agent_type == new_agent.agent_type).\
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

    def remember(self, new_agent, body):
        session = meta.Session()

        # fixme: check for the presence of all these entries.
        try:
            entry = session.query(AgentStatusEntry).\
                filter(AgentStatusEntry.domainid == self.domainid).\
                filter(AgentStatusEntry.uuid == body['uuid']).\
                one()
            found = True
        except NoResultFound, e:
            found = False

        if not found or entry.displayname == None or entry.displayname == "":
            (displayname, display_order) = self.calc_new_displayname(new_agent)

        entry = AgentStatusEntry(body['hostname'],
                         new_agent.agent_type,
                         body['version'],
                         body['ip-address'],
                         body['listen-port'],
                         u'palette',     # fixme
                         u'tableau2014',
                         body['uuid'],
                         self.domainid)
        entry.last_connection_time = func.now()
        if not found:
            entry.displayname = displayname
            entry.display_order = display_order

        entry = session.merge(entry)
        session.commit()
        # Remember the yml contents
        if new_agent.yml_contents:
            self.update_agent_yml(entry.agentid, new_agent.yml_contents)

        # Remember the agent pinfo
        if not self.update_agent_pinfo(new_agent, entry.agentid):
            return False

        session.commit()
        return entry

    def update_agent_yml(self, agentid, yml_contents):
        """update the agent_yml table with this agent's yml contents."""
        session = meta.Session()
        # First delete any old entries for this agent
        entry = session.query(AgentYmlEntry).\
            filter(AgentYmlEntry.agentid == agentid).delete()

        # This the first line ('---')
        for line in yml_contents.strip().split('\n')[1:]:
            key, value = line.split(":", 1)
            entry = AgentYmlEntry(agentid=agentid, key=key, value=value)
            session.add(entry)

    def update_agent_pinfo(self, new_agent, agentid):
        pinfo = new_agent.pinfo

        session = meta.Session()
        # First delete any old entries for this agent
        session.query(AgentInfoEntry).\
            filter(AgentInfoEntry.agentid == agentid).delete()

        # Set all of the agent volumes to 'inactive'.
        # Each volume pinfo sent us will later be set to 'active'.
        session.query(AgentVolumesEntry).\
            filter(AgentVolumesEntry.agentid == agentid).\
                   update({"active" : False}, synchronize_session=False)

        parts = new_agent.auth['install-dir'].split(':')
        if len(parts) != 2:
            self.log.error("Bad format for install-dir: %s",
                                                new_agent.auth['install-dir'])
            return False
            
        install_dir_vol = parts[0]
        install_dir_path = parts[1]

        for key, value in pinfo.iteritems():
            if key != 'volumes':
                entry = AgentInfoEntry(agentid=agentid, key=key, value=value)
                session.add(entry)
                continue
            for volume in value:
                if 'name' in volume:
                    name = volume['name']
                else:
                    self.log.error("volume missing 'name' in pinfo for " + \
                        "agentid %d. Will ignore: %s", agentid, str(volume))
                    continue

                try:
                    entry = session.query(AgentVolumesEntry).\
                        filter(AgentVolumesEntry.agentid == agentid).\
                        filter(AgentVolumesEntry.name == name).\
                        filter(AgentVolumesEntry.primary_data_loc == False).\
                        one()
                    found = True
                except NoResultFound, e:
                    found = False

                if not found:
                    if 'type' in volume:
                        if volume['type'] == "Fixed":
                            # Set a default path for new "Fixed" volumes.
                            # (Only "Fixed" volumes can be used for an archive.)
                            volume['path'] = AgentConnection.DEFAULT_VOLUME_PATH

                        entry = AgentVolumesEntry.build(agentid, volume)
                        session.add(entry)
                else:
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

                if new_agent.agent_type == AgentManager.AGENT_TYPE_PRIMARY \
                                            and install_dir_vol == entry.name:

                    # Add or merge a volume for primary data dir
                    pri_data_dir = ntpath.join(install_dir_path,
                                                    AgentConnection.DATA_DIR)

                    try:
                        entry = session.query(AgentVolumesEntry).\
                            filter(AgentVolumesEntry.agentid == agentid).\
                            filter(AgentVolumesEntry.primary_data_loc == True).\
                            one()
                        found = True
                    except NoResultFound, e:
                        found = False

                    if not found:
                        entry = AgentVolumesEntry(agentid=agentid,
                            name=entry.name,
                            path=pri_data_dir,
                            vol_type=entry.vol_type,
                            drive_format=entry.drive_format,
                            size=entry.size,
                            available_space=entry.available_space,
                            system=entry.system,
                            archive=entry.archive,
                            archive_limit=entry.archive_limit,
                            primary_data_loc=True,
                            active=True
                        )
                        session.add(entry)
                    else:
                        entry.path=pri_data_dir
                        active=True

                        session.merge(entry)

        session.commit()

        return True

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
            entry = session.query(AgentStatusEntry).\
                filter(AgentStatusEntry.uuid == uuid).one()
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
        entry = session.query(AgentStatusEntry).\
            filter(AgentStatusEntry.agentid == agentid).\
            one()
        entry.last_disconnect_time = func.now()
        session.commit()

    # Return the list of all agents
    def all_agents(self):
        return self.agents

    def agent_connected(self, aconn):
        """Check to see if the passed agent is still connected.
        Returns:
            True if still conencted.
            False if not connected.
        """
        return aconn in self.agents.values()

    def agent_conn_by_type(self, agent_type):
        """Returns an instance of a connected agent of the requested type,
        or a list of instances if more than one agent of that type
        is connected.

        Returns None if no agents of that type are connected."""

        for key in self.agents:
            if self.agents[key].agent_type == agent_type:
                return self.agents[key]

        return None

    def agent_conn_by_displayname(self, target):
        """Search for a connected agent with a displayname of the
        passed target.

        Return an instance of it, or None if none match."""

        for key in self.agents:
            if self.agents[key].displayname == target:
                return self.agents[key]

        return None

    def agent_conn_by_hostname(self, target):
        """Search for a connected agent with a hostname of the
        passed target.

        Return an instance of it, or None if none match."""

        for key in self.agents:
            if self.agents[key].auth['hostname'] == target:
                return self.agents[key]

        return None

    def agent_conn_by_uuid(self, target):
        """Search for agents with the given uuid.
            Return an instance of it, or None if none match.
        """

        for key in self.agents:
            if self.agents[key].auth['uuid'] == target:
                return self.agents[key]

        return None

    def remove_agent(self, agent, reason="", send_alert=True):
        """Remove an agent.
            Args:
                agent:       The agent to remove.
                reason:      An optional message, describing why.
                send_alert:  True or False.  If True, sends an alert.
                             If False does not send an alert.
        """
        if reason == "":
            reason = "Agent communication failure"

        self.lock()
        uuid = agent.uuid
        if self.agents.has_key(uuid):
            self.log.debug("Removing agent with uuid %s, name %s, reason: %s",\
                uuid, self.agents[uuid].auth['hostname'], reason)

            if send_alert:
                self.server.alert.send(CustomAlerts.AGENT_DISCONNECT,
                    { 'error': reason,
                      'info': "\nAgent: %s\nAgent type: %s\nAgent uuid %s" %
                        (agent.displayname, agent.agent_type, uuid) } )

            self.forget(agent.agentid)
            self.log.debug("remove_agent: closing agent socket.")
            if self._close(agent.socket):
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

            tobj = threading.Thread(target=self.new_agent_connection,
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
            if agent.socket.fileno() == fd:
                self.log.debug("Agent closed connection for: %s", key)
                agent.socket.close()
                del self.agents[key]
                return

        self.log.error("Couldn't find agent with fd: %d", fd)

    # thread function: spawned on a new connection from an agent.
    def new_agent_connection(self, conn, addr):
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
            agent = AgentConnection(self.server, conn, addr)

            # sleep for 100ms to prevent:
            #  'An existing connection was forcibly closed by the remote host'
            # on the Windows client when the agent tries to connect.
            time.sleep(.1);

            httpconn = ReverseHTTPConnection(conn)

            # Send the 'auth 'command.
            httpconn.request('POST', '/auth')

            res = httpconn.getresponse()
            print >> sys.stderr, 'command: auth: ' + str(res.status) + ' ' + str(res.reason)
            # Get the auth reply.
            self.log.debug("new_agent_connection: about to read.")
            body_json = res.read()
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

            agent.httpconn = httpconn
            agent.auth = body

            if self.server.init_new_agent(agent):
                self.register(agent, body)
                self.save_routes(agent) # fixme: check return value?
            else:
                self.log.error("Bad agent.  Disconnecting.")
                self._close(conn)
                return

        except socket.error, e:
            self.log.debug("Socket error: " + str(e))
            self._close(conn)
        except Exception, e:
            self.log.error("Exception:")
            traceback.format_exc()
            self.log.error(str(e))
            self.log.error(traceback.format_exc())

    def save_routes(self, agent):
        lines = ""
        rows = meta.Session().query(AgentVolumesEntry).\
            filter(AgentVolumesEntry.agentid == agent.agentid).\
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

        if 'install-dir' not in agent.auth:
            self.log.error("save_routes: agent is missing 'install-dir'")
            return

        route_path = ntpath.join(agent.auth['install-dir'], "conf", "archive",
                                                                "routes.txt")
        try:
            agent.filemanager.put(route_path, lines)
        except (exc.HTTPException, httplib.HTTPException,
                                                    EnvironmentError) as e:
            self.log.error(\
                "filemanager.put(%s) on %s failed with: %s",
                                    agent.displayname, route_path, str(e))
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
                self.log.debug("no agents to ping")
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
                body = self.server.ping(agent)
                if body.has_key('error'):
                    self.log.info("Ping: Agent '%s', type '%s', uuid %s did not respond to ping.  Removing." %
                        (agent.displayname, agent.agent_type, key))

                    self.manager.remove_agent(agent, "Lost contact with an agent")
                else:
                    self.log.debug("Ping: Reply from agent '%s', type '%s', uuid %s." %
                        (agent.displayname, agent.agent_type, key))

            time.sleep(self.ping_interval)
