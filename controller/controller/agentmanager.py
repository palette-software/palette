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

from agentstatus import AgentStatusEntry
from state import StateManager, StateEntry

import meta
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func
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
    CERT_FILE_DEFAULT = "/etc/palette_cert.pem"

    # Agent types
    AGENT_TYPE_PRIMARY="primary"
    AGENT_TYPE_WORKER="worker"
    AGENT_TYPE_OTHER="other"

    DEFAULT_INSTALL_DIR = "c:\\Program Files (x86)\\Palette\\"

    def __init__(self, server, host='0.0.0.0', port=0):
        super(AgentManager, self).__init__()
        self.server = server
        self.config = self.server.config
        self.log = self.server.log
        self.domainid = self.server.domainid
        self.Session = sessionmaker(bind=meta.engine)
        self.daemon = True
        self.lockobj = threading.RLock()
        self.host = host
        self.port = port and port or self.PORT
        self.socket = None
        self.auth = None
        # A dictionary with all AgentConnections with the key being
        # the unique 'conn_id'.
        self.agents = {}

        self.ssl = self.config.getboolean('controller','ssl', default=False)
        if self.ssl:
            if self.config.has_option('controller', 'ssl_cert_file'):
                self.cert_file = self.config.get('controller', 'ssl_cert_file')
            else:
                self.cert_file = self.CERT_FILE_DEFAULT
            if not os.path.exists(self.cert_file):
                self.log.critical("ssl enabled, but ssl certificate file does not exist: %s", self.cert_file)
                raise IOError("Certificate file not found: " + self.cert_file)

    def update_last_disconnect_time(self):
        """Called during startup to set a disconnection time for agents that
           were still connected when we stopped."""

        session = self.Session()

        try:
            session.query(AgentStatusEntry).\
                filter(AgentStatusEntry.last_connection_time > \
                  AgentStatusEntry.last_disconnect_time).\
                update({"last_disconnect_time" : func.now()},
                  synchronize_session=False)
            session.commit()
        finally:
            session.close()

    def register(self, new_agent, body):
        """Called with the agent object and body /auth dictionary that
           was sent from the agent in json."""
       
        self.lock()
        self.log.debug("new agent of type: %s, name %s, uuid %s, conn_id %d", body['type'], body['hostname'], body['uuid'], new_agent.conn_id)

        new_agent_type = body['type']
        # Don't allow two primary agents to be connected and
        # don't allow two agents with the same name to be connected
        # Keep the newest one.
        for key in self.agents.keys():
            agent = self.agents[key]
            if agent.uuid == body['uuid']:
                self.log.info("Agent already connected with name '%s': will remove it and use the new connection.", body['uuid'])
                self.remove_agent(agent)
                break
            elif new_agent_type == AgentManager.AGENT_TYPE_PRIMARY and \
                                agent.auth['type'] == AgentManager.AGENT_TYPE_PRIMARY:
                    self.log.info("Primary agent already connected: will remove it and keep the new primary agent connection.")
                    self.remove_agent(agent)

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

        self.unlock()

    # formerly agentstatus.add()
    def remember(self, body):
        session = self.Session()

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

        # Since we merged, we cannot return entry after session.close()
        # because we will get an "unbound" error, so get a fresh entry
        # that we can return.
        try:
            entry = session.query(AgentStatusEntry).\
                filter(AgentStatusEntry.uuid == body['uuid']).one()
        finally:
            session.close()

        return entry

    def set_displayname(self, hostname, displayname):
        error = ""

        session = self.Session()
        try:
            entry = session.query(AgentStatusEntry).\
                filter(AgentStatusEntry.hostname == hostname).one()
            entry.displayname = displayname
            session.merge(entry)
            session.commit()
        except NoResultFound, e:
            error = "No agent found with hostame=%s" % (hostname)
        finally:
            session.close()

        return error

    def forget(self, agentid):
        session = self.Session()
        #fixme: add try
        entry = session.query(AgentStatusEntry).\
            filter(AgentStatusEntry.agentid == agentid).\
            one()
        entry.last_disconnect_time = func.now()
        session.commit()
        session.close()

    # Return the list of all agents
    def all_agents(self):
        return self.agents

    def agent_conn_by_type(self, agent_type):
        """Returns an instance of an Agent of the requested type."""
        for key in self.agents:
            if self.agents[key].auth['type'] == agent_type:
                return self.agents[key]

        return False

    def agent_conn_by_name_or_type(self, target):
        """Search if a target is a displayname or agent type and
        return an instance of it, or False if none match."""

        for key in self.agents:
            if self.agents[key].displayname == target:
                return self.agents[key]

            if self.agents[key].auth['type'] == target:
                return self.agents[key]

        return False


    def lock_agent(self, agent):
        agent.lock()

    def unlock_agent(self, agent):
        agent.unlock()

    def remove_agent(self, agent):
        self.lock()
        conn_id = agent.conn_id
        if self.agents.has_key(conn_id):
            self.log.debug("Removing agent with conn_id %d, name %s",\
                conn_id, self.agents[conn_id].auth['hostname'])
            self.forget(agent.agentid)
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
        self.raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM);
        self.raw_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.raw_socket.bind((self.host, self.port))
        self.raw_socket.listen(8)

        if self.ssl:
            self.socket = ssl.wrap_socket(self.raw_socket, server_side=True,
                                                       certfile=self.cert_file)
        else:
            self.socket = self.raw_socket

        # Start socket monitor check thread
        asocketmon = AgentSocketMonitor(self, self.log)
        asocketmon.start()

        while True:
            try:
                conn, addr = self.socket.accept()
            except (ssl.SSLError, socket.error), e:
                # http://bugs.python.org/issue9211, though takes
                # a while to garbage collect and close the fd.
                self.log.debug("Client ssl negotiation failed. Closing socket.")
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
            required = ['hostname', 'type', 'ip-address', 'version', 'listen-port', 'uuid']
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

class AgentSocketMonitor(threading.Thread):

    def __init__(self, manager, log):
        super(AgentSocketMonitor, self).__init__()
        self.manager = manager
        self.log = log

    def run(self):

        self.log.debug("Starting socket monitor.")
        return # fixme - change after windows Agent works

        while True:
            if len(self.manager.agents) == 0:
                # no agents to check on
                time.sleep(3)   # fixme
                continue

            # Agents are allowed to send us data only as a response
            # to a controller command.  So if if there is an EPOLLIN
            # event, after we have the manager lock, it means the
            # Agent has disconnected.
            input = []

            self.manager.lock()
            agents = self.manager.agents
            for key in agents:
                self.log.debug("Socket monitor check for agent type: " + key)
                input.append(agents[key].socket)

            self.log.debug("about to poll")
            input_ready, output_ready, except_ready = select.select(input, [], [],0)
            for sock in input_ready:
                fd = sock.fileno()
                self.manager.socket_fd_closed(fd)

            self.manager.unlock()
            time.sleep(3) # fixme: shorten for production
