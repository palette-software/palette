import sys
import socket
import json

from SocketServer import TCPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
import urlparse

from agentmanager import AgentManager
from inits import *

version="0.1"

# A Palette Windows Agent.

# Accepts commands from the Controller and sends replies.
# The body of the request and response is JSON.
class AgentHandler(SimpleHTTPRequestHandler):

    agent_hostname = "one"
    agent_type = AGENT_TYPE_PRIMARY
    agent_ip = "192.168.1.2"

    get_status_count = 0

    # Override BaseHTTPRequestHandler call to socket.getfqdn
    # AgentHandler inherits from SimpleHTTPRequestHandler, which
    # inherits from BaseHTTPRequestHandler which calls socket.getfqdn
    # when it composes a response. There is a bug that can cause a
    # delay (we saw 10 second delays) when socket.getfqdn tries to
    # get a FQDN for localhost. The bug is described here:
    #
    #   http://bugs.python.org/issue6085
    #
    # and here:
    #
    #   http://www.answermysearches.com/xmlrpc-server-slow-in-python-how-to-fix/2140
    def _bare_address_string(self):
        host, port = self.client_address[:2]
        return '%s' % host
    address_string = _bare_address_string

    # The "auth" immediate command reply.
    # Immediate commands methods begin with 'icommand_'.
    def icommand_auth(self):
        body_dict = { "domain": "test-domain",
                "username": "palette-username",
                "password": "secret",
                "version": version,
                "hostname": AgentHandler.agent_hostname,
                "type": AgentHandler.agent_type,
                "ip-address": AgentHandler.agent_ip,
                "listen-port": 12345,
                "uuid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxx1",
            }

        return body_dict

    def command_cli(self, in_body_dict):
        """[Pretend to] Start a process for the cli command."""
        
        if not in_body_dict.has_key('action'):
            raise HttpException(405)    #fixme (not 405)

        action = in_body_dict['action']

        if action == 'cleanup':
            return { "xid": in_body_dict["xid"], 
                     "run-status": "running"}

        elif action != 'start':
            raise HttpException(405)    #fixme (not 405)

        # pretend we started...
        return { "xid": in_body_dict["xid"], 
                     "run-status": "running"}

    def command_get(self, in_body_dict):
        """[Pretend to] do the 'get' command."""
        return self.command_cli(in_body_dict)  # Pretends the same as cli commnand

    def get_status(self, xid):
        """Return the status of a request with the passed xid."""
        # For now, return the same status for every request.

        AgentHandler.get_status_count += 1
        print "count:", AgentHandler.get_status_count
        if AgentHandler.get_status_count % 2 == 0:
            # report still running
            outgoing_body_dict = {
                "run-status": "running",
                "xid": xid }

        else:
            # send finished
            outgoing_body_dict = {
                "run-status": "finished",
                "exit-status": 0,
                "xid": xid,
                "stdout": "this is stdout from the command",
                "stderr": "" }

        return outgoing_body_dict

    # Parses the incoming commmand from the Controller.
    # Returns the response_code to send.
    # Sets 'self.response_body' to the body to return.
    def parse_command(self, method):

        self.response_body = ""

        if self.path[0] != '/':
            print "Missing '/' in URI:", self.path
            raise HttpException(404)

        icommand = self.path[1:]
        print "icommand =", icommand

        if method == 'GET':
            print 'loc 1'
            # check for a valid command
            # Example: "GET /cli?xid=123"
            parts = urlparse.urlparse(self.path)

            if not parts.path in ["/cli", "/get", "sql", "/no-op"]:

                print "Unknown GET command:", parts.path
                raise HttpException(404)

            print 'loc 2'
            print 'query = ', parts.query
            query_dict = urlparse.parse_qs(parts.query)
            if query_dict.has_key("xid"):
                xid = int(query_dict['xid'][0])
                return self.get_status(xid)
            else:
                print "bad query string:", query
                raise HttpException(405)    # fixme

        # Immediate commands
        icommand_function = getattr(self, 'icommand_' + self.path[1:], None)
        print "icommand_function:", icommand_function

        # It's an "immediate" command:  The complete result is
        # sent in the reply.
        if icommand_function:
            return icommand_function()

        # It is a "Standard" command.  We start the command, but
        # we won't return the results until later, after the
        # command has finished.
        if not self.headers.has_key('Content-length'):
            print "Missing body in request", self.headers
            raise HttpException(405)    # fixme - not 405

        content_length = int(self.headers['Content-Length'])

        print "about to read", content_length
        incoming_json = self.rfile.read(content_length)
        print "read incoming_json:", incoming_json
        try:
            body_dict = json.loads(incoming_json)
        except:
            print "Bad json:", incoming_json
            raise HttpException(405)    # fixme - not 405

        command = self.path[1:]

        command_function = getattr(self, 'command_' + command, None)
        if command_function:
            return command_function(body_dict)
        else:
            print "Unknown command:", command
            raise HttpException(404)

    def handle_controller_command(self, method):
        response_code = 200
        body_dict = {}

        try:
            body_dict = self.parse_command(method)
        except HttpException, e:
            response_code = e.status_code

        print "response_code:", response_code, "body_dict:", body_dict

        if len(body_dict):
            response_body = json.dumps(body_dict)
        else:
            response_body = ""

        self.send_response(response_code)
        self.send_header("Content-Length", len(response_body))
        self.end_headers()
        self.wfile.write(response_body)
        print "sent in body reply:", response_body
        self.close_connection = 0

    def do_GET(self):
        print 'GET: '+self.path
        self.handle_controller_command("GET")
        return None

    def do_POST(self):
        print 'POST: '+self.path
        self.handle_controller_command("POST")
        return None

class Agent(TCPServer):

    def __init__(self, host='localhost', port=0):
        self.host = host
        self.port = port and port or AgentManager.PORT
        print "AGENT connecting to port", self.port

        # Start the Agent server that uses AgentHandler to handle
        # incoming requests from the Controller.
        TCPServer.__init__(self, (self.host, self.port), AgentHandler,
                           bind_and_activate=False)
        # Connect to the Controller.
        self.socket.connect((self.host, self.port))

    def get_request(self):
        return (self.socket, 'localhost')

class HttpException(Exception):
    def __init__(self, status_code):
        self.status_code = status_code

if __name__ == '__main__':

    if len(sys.argv) == 4:
        AgentHandler.agent_hostname = sys.argv[1]
        AgentHandler.agent_type = sys.argv[2]
        AgentHandler.agent_ip = sys.argv[3]
    elif len(sys.argv) != 1:
        print "usage: agent hostname {primary|worker|other} ip-address"
        sys.exit(1)

    httpd = Agent()
    httpd.serve_forever()
