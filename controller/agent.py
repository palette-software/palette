import sys
import socket
import threading

from httplib import HTTPConnection
from SocketServer import TCPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler

class AgentConnection(object):
    
    def __init__(self, conn, addr):
        self.socket = conn
        self.addr = addr

class AgentManager(threading.Thread):

    PORT = 8080

    def __init__(self, host='localhost', port=0):
        super(AgentManager, self).__init__()
        self.daemon = True
        self.host = host
        self.port = port and port or self.PORT
        self.socket = None
        self.agents = []

    def register(self, agent):
        self.agents.append(agent)

    def run(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM);
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(8)

        while True:
            conn, addr = self.socket.accept()
            agent = AgentConnection(conn, addr)

            httpconn = ReverseHTTPConnection(conn)
            httpconn.request('GET', '/auth')
            res = httpconn.getresponse()
            print >> sys.stderr, 'GET /auth: ' + str(res.status) + ' ' + str(res.reason)
            
            self.register(agent)

class ReverseHTTPConnection(HTTPConnection):
    
    def __init__(self, s):
        HTTPConnection.__init__(self, 'agent')
        self.sock = s
    
    def connect(self):
        pass

    def close(self):
        pass
        

# DEBUGGING ONLY BEYOND THIS POINT

class AgentHandler(SimpleHTTPRequestHandler):
    
    def do_GET(self):
        print >> sys.stderr, 'GET: '+self.path
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()
        self.close_connection = 0
        return None
        

class Agent(TCPServer):

    def __init__(self, host='localhost', port=0):
        self.host = host
        self.port = port and port or AgentManager.PORT
        TCPServer.__init__(self, (self.host, self.port), AgentHandler,
                           bind_and_activate=False)
        self.socket.connect((self.host, self.port))

    def get_request(self):
        return (self.socket, 'localhost')

if __name__ == '__main__':
    httpd = Agent()
    httpd.serve_forever()
