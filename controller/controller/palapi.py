import os
import sys
import socket
import json
import hashlib
import ntpath
import posixpath

class UpgradeException(Exception):
    def __init__(self, errmsg):
        Exception.__init__(self, errmsg)

class UpgradeHandler(object):
    def __init__(self, args):
        self.args = args

        self.connected = False

        self.preamble = "/envid=%d" % (args.envid)

        if args.displayname:
            self.preamble += ' /displayname="%s"' % (args.displayname)
            self.spec_str = "displayname"
            self.spec_val = args.displayname
        elif args.uuid:
            self.preamble += ' /uuid=%s' % (args.uuid)
            self.spec_str = "uuid"
            self.spec_val = args.uuid
        elif args.agent_type:
            self.preamble += ' /type=%s' % (args.agent_type)
            self.spec_str = "type"
            self.spec_val = self.args

    def connect(self):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.conn.connect((self.args.hostname, self.args.port))
        except socket.error, e:
            raise UpgradeException(\
                ("Could not connect to host '%s', port '%d': %s") %
                                (self.args.hostname, self.args.port, e))

        self.sock = self.conn.makefile('w+', 1)
        self.connected = True

    def send_cmd(self, cmd, sync=False):

        if not self.connected:
            self.connect()

        self.command = cmd
        self.ack = ""
        self.response = ""
        self.result = {}
        self.status = ""

        if self.args.verbose > 2:
            print "Sending command:", cmd
        self.full_command = self.preamble + ' ' + cmd
        self.sock.write(self.full_command +'\n')
        self.sock.flush()
        self.ack = self.sock.readline().strip()
        if self.args.verbose > 2:
            print "Acknowledgment response:", self.ack
        if self.ack != 'OK':
            raise UpgradeException("Command '%s' failed: %s" % \
                                        (self.command, self.ack))

        if self.args.verbose > 2:
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

        if self.args.verbose > 2:
            print 'Response:', self.response

        if 'error' in self.result:
            raise UpgradeException(\
                ('Error in command ("%s") response: %s') % \
                            (self.full_command, self.result['error']))

        if not 'status' in self.result:
            raise UpgradeException(\
                ('Error in command ("%s").  Missing "status" in ' + \
                  'response: %s') % \
                            (self.full_command, str(self.result)))

        if self.result['status'] != "OK":
            raise UpgradeException(\
                ('Error in command ("%s").  status not "OK" in ' + \
                  'response: %s') % \
                            (self.full_command, self.result['status']))


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

        if not len(self.result['agents']):
            raise UpgradeException("No agents connected now: %s." % \
                                                        self.result)

        for agent in self.result['agents']:
            if (self.args.displayname and agent['displayname'] == \
                                                    self.args.displayname) \
                or (self.args.uuid and agent['uuid'] == self.args.uuid) \
                    or (self.args.agent_type and agent['agent-type'] == \
                                                        self.args.agent_type):

                required = ['os-version',
                            'install-dir']
                for item in required:
                    if not item in agent:
                        raise UpgradeException(\
                            "Missing required key '%s' in '%s'" % \
                                                        (item, str(agent)))

                if 'microsoft' in agent['os-version'].lower():
                    agent['iswin'] = True
                    agent['path'] = ntpath
                else:
                    agent['iswin'] = False
                    agent['path'] = posixpath
                return agent

        raise UpgradeException("Agent not found: %s %s" % \
                                        (self.spec_str, self.spec_val))
