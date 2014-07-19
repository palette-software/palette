import os
import sys
import socket
import ssl
import json
import time
import argparse

import platform
import multiprocessing
import shutil

import ConfigParser as configparser

from SocketServer import TCPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
import urlparse

from config import Config
from apache2 import Apache2
from processmanager import ProcessManager
import logger

from util import version, str2bool

import http
from http import HTTPRequest, HTTPResponse

# Accepts commands from the Controller and sends replies.
# The body of the request and response is JSON.
class AgentHandler(SimpleHTTPRequestHandler):

    # Over-written in main()
    agent_hostname = "one"
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

    def memtotal(self):
        """ Read the MemTotal line from /proc/meminfo """
        try:
            with open('/proc/meminfo') as f:
                for line in f:
                    tokens = line.split()
                    if len(tokens) == 3 and tokens[0].lower() == 'memtotal:':
                        return int(tokens[1]) * 1024
        except IOError, ValueError:
            return -1
        return 0

    def handle_cli(self, req):
        if req.method == 'POST':
            try:
                action = req.json['action'].lower()
                xid = int(req.json['xid'])
            except (TypeError, KeyError, TypeError):
                raise http.HTTPBadRequest()
            if action == 'start':
                if not 'cli' in req.json:
                    raise http.HTTPBadRequest()
                cmd = req.json['cli']
                self.server.log.info('CMD['+str(xid)+']: '+cmd)
                if 'immediate' in req.json:
                    immediate = req.json['immediate']
                else:
                    immediate = False
                env = 'env' in req.json and req.json['env'] or {}
                self.server.processmanager.start(xid, cmd, env, immediate)
                data = self.server.processmanager.getinfo(xid)
            elif action == 'cleanup':
                self.server.processmanager.cleanup(xid)
                data = {'xid': xid}
            else:
                raise http.HTTPBadRequest()
        elif req.method == 'GET':
            try:
                xid = int(req.query['xid'][0])
            except (ValueError, KeyError, TypeError):
                raise http.HTTPBadRequest()
            data = self.server.processmanager.getinfo(xid)
        else:
            raise http.HTTPBadRequest()

        if 'run-status' in data and data['run-status'] == 'finished':
            self.server.log.info('JSON: ' + json.dumps(data))
        else:
            self.server.log.debug('JSON: ' + json.dumps(data))
        return data

    def handle_archive(self, req):
        if req.method != 'POST':
            raise http.HTTPMethodNotAllowed(req.method)
        if not 'action' in req.json:
            raise http.HTTPBadRequest()
        action = req.json['action'].lower()
        if action == 'start':
            if 'port' in req.json:
                self.server.archive.setport(req.json['port'])
            self.server.archive.start()
        elif action == 'stop':
            self.server.archive.stop()
        else:
            raise http.HTTPBadRequest()
        return {'status':'ok', 'port':self.server.archive.port }

    def get_path_from_query(self, req):
        if 'path' not in req.query:
            raise HTTPBadRequest("'path' is required.")
        if len(req.query['path']) != 1:
            raise HTTPBadRequest("'path' must be unique.")
        return req.query['path'][0]

    # The "auth" immediate command reply.
    # Immediate commands methods begin with 'icommand_'
    def handle_auth(self, req):
        d = { "license-key": self.server.license_key,
              "version": self.server.version,
              "os-version": platform.platform(),
              "processor-type": platform.processor(),
              "processor-count": multiprocessing.cpu_count(),
              "installed-memory": self.memtotal(),
              "hostname": socket.gethostname(),
              "fqdn": socket.getfqdn(),
              "ip-address": self.server.socket.getsockname()[0],
              "listen-port": self.server.archive_port,
              "uuid": self.server.uuid,
              "install-dir": self.server.install_dir,
              # FIXME
              "data-dir": self.server.data_dir
            }
        return d

    def handle_file_GET(self, req):
        path = self.get_path_from_query(req)
        if not os.path.isfile(path):
            raise HTTPNotFound(path)
        res = req.response
        # FIXME: catch IOError, OSError
        res.setfile(open(path, 'r'))
        res.set_content_length()
        return res

    def handle_file_PUT(self, req):
        path = self.get_path_from_query(req)
        # FIXME: catch IOError, OSError
        with open(path, 'w') as f:
            if req.content_length:
#                FYI: this hangs:
#                shutil.copyfileobj(req.rfile, f, req.content_length)
                # fixme: check to make sure all was read?
                data = req.rfile.read(req.content_length)
                f.write(data)
        return req.response

    def handle_file_DELETE(self, req):
        path = self.get_path_from_query(req)
        # FIXME: test for OSError
        os.remove(path)
        return req.response

    def handle_file(self, req):
        if req.method == 'GET':
            return self.handle_file_GET(req)
        if req.method == 'PUT':
            return self.handle_file_PUT(req)
        if req.method == 'DELETE':
            return self.handle_file_DELETE(req)
        raise HTTPBadRequest()

    def handle_method(self, method):
        self.server.log.info(method +' ' + self.path)
        res = None
        try:
            req = HTTPRequest(self, method)
            if req.path == '/archive':
                res = self.handle_archive(req)
            elif req.path == '/auth':
                res = self.handle_auth(req)
            elif req.path == '/cli':
                res = self.handle_cli(req)
            elif req.path == '/file':
                res = self.handle_file(req)
            elif req.path == '/ping':
                res = req.response
            else:
                raise http.HTTPNotFound(req.path)
        except http.HTTPException, e:
            e.handler = self
            res = e
        
        if res == None:
            res = http.HTTPNotFound(path)
        elif isinstance(res, HTTPResponse):
            pass
        elif isinstance(res, basestring):
            s = res
            res = req.response
            res.wfile.write(s)
        else: # Everything else is converted to JSON
            obj = res
            res = req.response
            res.content_type = 'application/json'
            res.wfile.write(json.dumps(obj))

        # terminate the request
        req.close()
        # send it
        res.flush()

    def do_GET(self):
        return self.handle_method('GET')

    def do_POST(self):
        return self.handle_method('POST')

    def do_PUT(self):
        return self.handle_method('PUT')

class Agent(TCPServer):

    LOGGER_NAME = 'main'
    DEFAULT_SECTION = 'DEFAULT'
    DEFAULT_LICENSE_KEY = "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
    DEFAULT_DATA_DIR = "/var/palette"

    def __init__(self, config):
        self.config = config
        self.host = config.get('controller', 'host', default='localhost')
        self.port = config.getint('controller', 'port', default=8888)
        self.ssl = config.getboolean('controller', 'ssl', default=True)
        self.data_dir = config.get('controller', 'data-dir',
                                            default=self.DEFAULT_DATA_DIR)

        if not os.path.isdir(self.data_dir):
            os.mkdir(self.data_dir)
        for sub_dir in ["data", "archive", "logs/archive"]:
            tdir = os.path.join(self.data_dir, sub_dir)
            if not os.path.isdir(tdir):
                os.makedirs(tdir)

        self.uuid = config.get(self.DEFAULT_SECTION, 'uuid')
        self.version = version()
        self.license_key = config.get(self.DEFAULT_SECTION, 'license-key', 
                                      default=self.DEFAULT_LICENSE_KEY)
        self.archive_port = config.get('archive', 'port', default=8889)

        self.install_dir = os.path.abspath(os.path.dirname(__file__))
        self.xid_dir = config.get(self.DEFAULT_SECTION, 'xid-dir',
                                  default=None)
        if not self.xid_dir:
            self.xid_dir = os.path.join(self.install_dir, 'xid')
        if not os.path.isdir(self.xid_dir):
            os.mkdir(self.xid_dir)

        pathenv = config.get(self.DEFAULT_SECTION, 'path', default=None)
        self.processmanager = ProcessManager(self.xid_dir, pathenv)

        conf = os.path.join(self.install_dir, 'conf', 'archive', 'httpd.conf')
        port = config.getint("archive", "port", default=8889);
        self.archive = Apache2(conf, port, self.data_dir)

        # Start the Agent server that uses AgentHandler to handle
        # incoming requests from the Controller.
        TCPServer.__init__(self, (self.host, self.port),
                           AgentHandler, bind_and_activate=False)

    def connect(self):
        # Connect to the Controller.
        self.socket.connect((self.host, self.port))

        if self.ssl:
            self.socket = ssl.wrap_socket(self.socket)

    def get_request(self):
        return (self.socket, 'localhost')

class HttpException(Exception):
    def __init__(self, status_code):
        self.status_code = status_code

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Palette Agent.")
    parser.add_argument('config', nargs='?', default=None)

    args = parser.parse_args()

    config = Config(args.config)

    # loglevel is entirely controlled by the INI file.
    logger.make_loggers(config)
    log = logger.get(Agent.LOGGER_NAME)

    agent = Agent(config)
    agent.log = log
    log.info("Agent version: %s", agent.version)

    agent.connect()
    log.info("connected to %s:%d%s", agent.host, agent.port, \
                 agent.ssl and ' [SSL]' or '')
    agent.serve_forever()
