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

from agentstatus import AgentStatusEntry
from state import StateManager, StateEntry
from alert import Alert

import meta
from sqlalchemy import func, or_
from sqlalchemy.orm.exc import NoResultFound

# The Controller's Agent Manager.
# Communicates with the Agent.
# fixme: maybe merge with the AgentStatusEntry class.
class AgentConnection(object):
    
    _CID = 1

    def __init__(self, conn, addr):
        self.socket = conn
        self.addr = addr
        self.httpconn = False   # Used by the controller
        self.auth = {}          # Used by the controller
        self.agentid = None
        self.uuid = None

        # Each agent connection has its own lock
        self.lockobj = threading.RLock()

        # unique identifier
        # can never be 0
        self.conn_id = AgentConnection._CID
        AgentConnection._CID += 1
        if AgentConnection._CID == 0:
            AgentConnection._CID += 1

    def lock(self):
        self.lockobj.acquire()

    def unlock(self):
        self.lockobj.release()

    def set_httpconn(self, httpconn):
        self.httpconn = httpconn    # Used by the controller

    def set_auth(self, auth):
        self.auth = auth            # Used by the controller

class AgentManager(threading.Thread):

    PORT = 8888

    SSL_HANDSHAKE_TIMEOUT_DEFAULT = 5

    # Agent types
    AGENT_TYPE_PRIMARY="primary"
    AGENT_TYPE_WORKER="worker"
    AGENT_TYPE_OTHER="other"

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
        self.auth = None
        # A dictionary with all AgentConnections with the key being
        # the unique 'conn_id'.
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
       
        self.lock()
        self.log.debug("new agent of type: %s, name %s, uuid %s, conn_id %d", body['type'], body['hostname'], body['uuid'], new_agent.conn_id)

        new_agent_type = body['type']
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
                                agent.auth['type'] == AgentManager.AGENT_TYPE_PRIMARY:
                    self.log.info("A primary agent is already connected: will remove it and keep the new primary agent connection.")
                    self.remove_agent(agent, "A primary agent is already connected: will remove it and keep the new primary agent connection.", send_alert=False)

        # Remember the new agent
        entry = self.remember(body)
        if entry:
            new_agent.agentid = entry.agentid
            new_agent.uuid = entry.uuid
            new_agent.displayname = entry.displayname
        else:
            # FIXME: handle this as an error
            pass
        self.agents[new_agent.conn_id] = new_agent

        if new_agent_type == AgentManager.AGENT_TYPE_PRIMARY:
            self.log.debug("register: Initializing state entries on connect")
            stateman = StateManager(self.server)
            stateman.update(StateEntry.STATE_TYPE_MAIN, \
              StateEntry.STATE_MAIN_UNKNOWN)
            stateman.update(StateEntry.STATE_TYPE_BACKUP, \
              StateEntry.STATE_BACKUP_NONE)

            # Tell the status thread to start getting status on
            # the new primary.
            self.new_primary_event.set()

        self.unlock()

    # formerly agentstatus.add()
    def remember(self, body):
        session = meta.Session()

        # fixme: check for the presence of all these entries.
        entry = AgentStatusEntry(body['hostname'],
                                 body['type'], 
                                 body['version'], 
                                 body['ip-address'],
                                 body['listen-port'],
                                 body['uuid'],
                                 self.domainid)
        entry.last_connection_time = func.now()
        entry = session.merge(entry)
        if entry.displayname == None or entry.displayname == "":
            entry.displayname = entry.hostname
            entry = session.merge(entry)
        session.commit()
        return entry

    def set_displayname(self, aconn, uuid, displayname):
        session = meta.Session()
        try:
            entry = session.query(AgentStatusEntry).\
                filter(AgentStatusEntry.uuid == uuid).one()
            entry.displayname = displayname
            session.merge(entry)
            session.commit()
            if aconn:
                aconn.auth['displayname'] == displayname
        except NoResultFound, e:
            raise ValueError('No agent found with uuid=%s' % (uuid))

    def forget(self, agentid):
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
            if self.agents[key].auth['type'] == agent_type:
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

    def lock_agent(self, agent):
        agent.lock()

    def unlock_agent(self, agent):
        agent.unlock()

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
        conn_id = agent.conn_id
        if self.agents.has_key(conn_id):
            self.log.debug("Removing agent with conn_id %d, name %s, reason: %s",\
                conn_id, self.agents[conn_id].auth['hostname'], reason)

            if send_alert:
                alert = Alert(self.config, self.log)
                alert.send(reason, "\nAgent: %s\nAgent type: %s\nAgent connection-id %d" % 
                            (agent.displayname, agent.auth['type'], conn_id))

            self.forget(agent.agentid)
            self.log.debug("remove_agent: closing agent socket.")
            try:
                agent.socket.close()
            except socket.error as e:
                self.log.debug("remove_agent: close agent socket failure:" + \
                                            str(e))
                pass
            else:
                self.log.debug("remove_agent: close agent socket succeeded.")

            del self.agents[conn_id]
        else:
            self.log.debug("remove_agent: No such agent with conn_id %d", conn_id)
        if agent.auth['type'] == AgentManager.AGENT_TYPE_PRIMARY:
            self.log.debug("remove_agent: Initializing state entries on removal")
            stateman = StateManager(self.server)
            stateman.update(StateEntry.STATE_TYPE_MAIN, \
              StateEntry.STATE_MAIN_UNKNOWN)
            stateman.update(StateEntry.STATE_TYPE_BACKUP, \
              StateEntry.STATE_BACKUP_NONE)

        self.unlock()

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
            agent = AgentConnection(conn, addr)

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
            self.log.debug("new_agent_connection reading....")
            body_json = res.read()
            if body_json:
                body = json.loads(body_json)
                self.log.debug("body = " + str(body))
            else:
                body = {}
                self.log.debug("done.")

            # Inspect the reply to make sure it has all the required values.
            required = ['hostname', 'type', 'ip-address', \
                            'version', 'listen-port', 'uuid', 'install-dir']
            for item in required:
                if not body.has_key(item):
                    self.log.error("Missing '%s' from agent" % item)
                    conn.close()
                    return

            agent_type = body['type']
            if agent_type not in [ AgentManager.AGENT_TYPE_PRIMARY,
              AgentManager.AGENT_TYPE_WORKER, AgentManager.AGENT_TYPE_OTHER ]:
                self.log.error("Bad agent type sent: " + agent_type)
                conn.close()
                return

            agent.set_httpconn(httpconn)
            agent.set_auth(body)

            self.register(agent, body)

        except socket.error, e:
            self.log.debug("Socket error: " + str(e))
            conn.close()
        except Exception, e:
            self.log.error("Exception:")
            traceback.format_exc()
            self.log.error(str(e))
            self.log.error(traceback.format_exc())

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
                    self.log.debug("agent with conn_id '%d' is now gone and won't be checked." % 
                        key)
                    self.manager.unlock()
                    continue
                agent = agents[key]
                self.manager.unlock()

                self.log.debug("Ping: check for agent '%s', type '%s', conn_id %d." % \
                        (agent.displayname, agent.auth['type'], key))

                # fixme: add a timeout ?
                body = self.server.ping(agent)
                if body.has_key('error'):
                    self.log.info("Ping: Agent '%s', type '%s', conn_id %d did not respond to ping.  Removing." %
                        (agent.displayname, agent.auth['type'], key))

                    self.manager.remove_agent(agent, "Lost contact with an agent")
                else:
                    self.log.debug("Ping: Reply from agent '%s', type '%s', conn_id %d." %
                        (agent.displayname, agent.auth['type'], key))
                    
            time.sleep(self.ping_interval)
