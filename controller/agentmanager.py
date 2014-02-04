import sys
import socket
import select
import threading
import time
import traceback
from httplib import HTTPConnection
import json

from inits import *

# The Controller's Agent Manager.
# Communicates with the Agent.

class AgentConnection(object):
    
    def __init__(self, conn, addr):
        self.socket = conn
        self.addr = addr
        self.httpconn = False
        self.auth = {}
        self.uuid = None
        self.ip = None

    def set_httpconn(self, httpconn):
        self.httpconn = httpconn

    def set_auth(self, auth):
        self.auth = auth

    def set_uuid(self, uuid):
        self.uuid = uuid

    def set_ip(self, ip):
        self.ip = ip

    def set_listen_port(self, listen_port):
        self.listen_port = listen_port

class AgentManager(threading.Thread):

    PORT = 8888

    def __init__(self, host='0.0.0.0', port=0):
        super(AgentManager, self).__init__()
        self.daemon = True
        self.lockobj = threading.Lock()
        self.host = host
        self.port = port and port or self.PORT
        self.socket = None

        # A dictionary with all AgentConnections
        # "primary" or "archive", etc.
        self.agents = {}

    def register(self, agent, agent_type):
        # fixme: What should we do if two primary agents connect?
        self.log.debug("Remembering new agent of type: "+ agent_type)
        self.agents[agent_type] = agent

    # Return the list of all agents
    def all_agents(self):
        return self.agents

    def agent_handle(self, agent_type):
        """Returns an instance of an Agent of the requested type."""
        if self.agents.has_key(agent_type):
            return self.agents[agent_type]

        return False

    def lock(self):
        self.lockobj.acquire()

    def unlock(self):
        self.lockobj.release()

    def run(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM);
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(8)

        # Start socket monitor check thread
        asocketmon = AgentSocketMonitor(self, self.log)
        asocketmon.start()

        while True:
            conn, addr = self.socket.accept()

            tobj = threading.Thread(target=self.new_agent_connection,
                                 args=(conn, addr))
            # Spawn a thread to handle the new agent connection
            tobj.start()

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
            required = ['hostname', 'type', 'ip-address', 'listen-port', 'uuid']
            for item in required:
                if not body.has_key(item):
                    self.log.error("Missing '%s' from agent" % item)
                    conn.close()
                    return

            agent_type = body['type']
            if agent_type not in [ AGENT_TYPE_PRIMARY,
                        AGENT_TYPE_WORKER, AGENT_TYPE_OTHER ]:
                self.log.error("Bad agent type sent: " + agent_type)
                conn.close()
                return

            agent.set_httpconn(httpconn)
            agent.set_auth(body)
            agent.set_uuid(body['uuid'])
            agent.set_ip(body['ip-address'])
            agent.set_listen_port(body['listen-port'])

            self.register(agent, agent_type)

        except socket.error, e:
            self.log.debug("Socket error")
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
