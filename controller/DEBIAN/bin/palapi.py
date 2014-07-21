import os
import sys
import socket
import argparse
import json
import hashlib
import ntpath
import posixpath

class UpgradeException(Exception):
    def __init__(self, errmsg):
        Exception.__init__(self, errmsg)

class UpgradeHandler(object):
    def __init__(self):
        parser = argparse.ArgumentParser(sys.argv[0])

        parser.add_argument('-v', '--verbose', dest='verbose',
                                                    action='store_true')
        parser.add_argument('--hostname', dest='hostname', default='localhost')
        parser.add_argument('--port', dest='port', type=int, default=9000)
        parser.add_argument('--envid', dest='envid', type=int, default=1)

        group1 = parser.add_mutually_exclusive_group(required=True)
        group1.add_argument('--target-dir', dest='target_dir')
        group1.add_argument('--console', '-c', dest='console',
                                                        action='store_true')

        group2 = parser.add_mutually_exclusive_group()
        group2.add_argument('--displayname', dest='displayname')
        group2.add_argument('--uuid', dest='uuid')
        group2.add_argument('--type', dest='agent_type', default='primary')

        parser.add_argument("newfile")

        args = parser.parse_args()

        self.verbose = args.verbose
        self.hostname = args.hostname
        self.port = args.port
        self.envid = args.envid
        self.newfile = os.path.abspath(args.newfile)

        self.console = args.console

        self.target_dir = args.target_dir

        self.displayname = args.displayname
        self.uuid = args.uuid
        self.agent_type = args.agent_type

        self.connected = False

        self.preamble = "/envid=%d" % (self.envid)

        if self.displayname:
            self.preamble += ' /displayname="%s"' % (self.displayname)
            self.spec_str = "displayname"
            self.spec_val = self.displayname
        elif self.uuid:
            self.preamble += ' /uuid=%s' % (self.uuid)
            self.spec_str = "uuid"
            self.spec_val = self.uuid
        elif self.agent_type:
            self.preamble += ' /type=%s' % (self.agent_type)
            self.spec_str = "type"
            self.spec_val = self.agent_type

    def connect(self):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.conn.connect((self.hostname, self.port))
        except socket.error, e:
            raise UpgradeException(\
                ("Could not connect to host '%s', port '%d': %s") %
                                (self.hostname, self.port, e))

        self.sock = self.conn.makefile('w+', 1)
        self.connected = True

    def send_cmd(self, cmd, sync=False):

        if not self.connected:
            self.connect()

        self.command = cmd
        self.status = ""
        self.response = ""
        self.result = {}

        if self.verbose:
            print "Sending command:", cmd
        self.full_command = self.preamble + ' ' + cmd
        self.sock.write(self.full_command +'\n')
        self.sock.flush()
        self.status = self.sock.readline().strip()
        if self.verbose:
            print "Status response:", self.status
        if self.status != 'OK':
            raise UpgradeException("Command '%s' failed: %s" % \
                                        (self.command, self.status))

        if self.verbose:
            print "Reading command response."
        self.response = self.sock.readline()

        try:
            self.result = json.loads(self.response)
        except ValueError as e:
            raise UpgradeException(\
                ("Can't decode input from command '%s' from " + \
                "response: '%s': %s") % (self.command, self.response, str(e)))
        finally:
            self._close()

        if self.verbose:
            print 'Response:', self.response

        if 'error' in self.result:
            raise UpgradeException(\
                ('Error in command ("%s") response: %s') % \
                            (self.full_command, self.result['error']))

    def _close(self):
        self.connected = False
        try:
            self.conn.shutdown(socket.SHUT_RDWR)
            self.conn.close()
            self.sock.close()
        except socket.error as e:
            print "Couldn't close socket. Ignoring."
            
    def checksum(self, path, buf_size=2**16):
        sha = hashlib.sha256()
        fd = open(path, "r")
        while True:
            data = fd.read(buf_size)
            if not data:
                break
            sha.update(data)

        fd.close()
        return sha.hexdigest()

    def get_agent_info(self):
        self.send_cmd("list")

        if not 'agents' in self.result:
            raise UpgradeException("Bad result from 'list' command: %s." % \
                                                        self.result)

        for agent in self.result['agents']:
            if (self.displayname and agent['displayname'] == \
                                                    self.displayname) \
                or (self.uuid and agent['uuid'] == self.uuid) \
                    or (self.agent_type and agent['agent_type'] == \
                                                        self.agent_type):

                required = ['os_version',
                            'install_dir']
                for item in required:
                    if not item in agent:
                        raise UpgradeException(\
                            "Missing required key '%s' in '%s'" % \
                                                        (item, str(agent)))

                if 'microsoft' in agent['os_version'].lower():
                    agent['iswin'] = True
                    agent['path'] = ntpath
                else:
                    agent['iswin'] = False
                    agent['path'] = posixpath
                return agent

        raise UpgradeException("Agent not found: %s %s" % \
                                        (self.spec_str, self.spec_val))
