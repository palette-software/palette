import sys
import argparse
import socket
import json
import hashlib
import ntpath
import posixpath

# FIXME: deprecate the use of 'store'
# pylint: disable=import-error,no-name-in-module
import akiri.framework.config as config
# pylint: enable=import-error,no-name-in-module

import clierror

class CommError(object):
    COULD_NOT_CONNECT_TO_HOST = 1
    COMMAND_FAILED_TO_RUN = 2
    COMMAND_RESULT_ERROR = 3    # The command resulted in an error

class CommException(StandardError):
    def __init__(self, errnum, message):
        StandardError.__init__(self, message)
        self.errnum = errnum
        self.message = message

class CommBase(object):
    # pylint: disable=too-many-instance-attributes
    def __init__(self):
        self.args = None

        self.hostname = None
        self.port = None
        self.envid = None

        self.preamble = ""

        self.connected = False
        self.sock = None
        self.conn = None
        self.command = ""
        self.result = ""
        self.response = ""

        # Defaults:
        self.spec_str = "type"
        self.spec_val = "primary"
        self.verbose = 1

    def connect(self):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.conn.connect((self.hostname, self.port))
        except socket.error, ex:
            raise CommException(CommError.COULD_NOT_CONNECT_TO_HOST,
                ("Could not connect to host '%s', port '%d': %s") %
                                (self.hostname, self.port, ex))

        self.sock = self.conn.makefile('w+', 1)
        self.connected = True

    # pylint: disable=too-many-branches
    def send_cmd(self, cmd, req=None, read_response=True,
                 skip_on_wrong_state=False):

        if not self.connected:
            self.connect()

        self.command = cmd
        self.response = ""
        self.result = {}

        if self.verbose > 1:
            print "Sending command:", cmd

        preamble = self.preamble
        if req:
            userid = req.remote_user.userid
            preamble += " /userid=%d" % userid

        full_command = preamble + ' ' + cmd
        self.sock.write(full_command +'\n')
        self.sock.flush()
        ack = self.sock.readline().strip()
        if self.verbose > 1:
            print "Acknowledgment response:", ack
        if ack != 'OK':
            parts = ack.split()
            if len(parts) < 2 or not parts[1].isdigit():
                raise CommException(CommError.COMMAND_FAILED_TO_RUN,
                                    "Command '%s' failed: %s" % \
                                        (self.command, ack))
            errnum = int(parts[1])
            # Skip on BUSY or WRONG_STATE if requested
            if skip_on_wrong_state and errnum in \
                            (clierror.ERROR_AGENT_NOT_FOUND,
                             clierror.ERROR_AGENT_NOT_CONNECTED,
                             clierror.ERROR_BUSY,
                             clierror.ERROR_WRONG_STATE,
                             clierror.ERROR_AGENT_NOT_FOUND):
                print >> sys.stderr, \
                    "Skipping command due to wrong state: '%s': %s" % \
                                                                    (cmd, ack)
                return

            raise CommException(CommError.COMMAND_FAILED_TO_RUN,
                                "Command '%s' failed. Error: %s" % \
                                    (self.command, ack))

        if not read_response:
            self._close()
            return

        if self.verbose > 1:
            print "Reading command response."
        self.response = self.sock.readline()

        try:
            self.result = json.loads(self.response)
        except ValueError as ex:
            raise CommException(CommError.COMMAND_FAILED_TO_RUN,
                ("Can't decode json from command '%s' from " + \
                "response: '%s': %s") % (self.command, self.response, str(ex)))
        finally:
            self._close()

        if self.verbose > 1:
            print 'Response:', self.response

        if 'error' in self.result:
            raise CommException(CommError.COMMAND_RESULT_ERROR,
                ('Error in command ("%s") response: %s') % \
                            (full_command, self.result['error']))

        if not 'status' in self.result:
            raise CommException(CommError.COMMAND_FAILED_TO_RUN,
                ('Error in command ("%s").  Missing "status" in ' + \
                  'response: %s') % \
                            (full_command, str(self.result)))

        if self.result['status'] != "OK":
            raise CommException(CommError.COMMAND_FAILED_TO_RUN,
                ('Error in command ("%s").  status not "OK" in ' + \
                  'response: %s') % \
                            (full_command, self.result['status']))


    def _close(self):
        self.connected = False
        try:
            self.conn.shutdown(socket.SHUT_RDWR)
            self.conn.close()
            self.sock.close()
        except socket.error:
            print "Couldn't close socket. Ignoring."

    def checksum(self, path, buf_size=2**16):
        sha = hashlib.sha256()
        fobj = open(path, "r")
        while True:
            data = fobj.read(buf_size)
            if not data:
                break
            sha.update(data)

        fobj.close()
        return sha.hexdigest()

    def get_agents(self):
        self.send_cmd("list")

        if not 'agents' in self.result:
            raise CommException(CommError.COMMAND_FAILED_TO_RUN,
                                "Bad result from 'list' command: %s." % \
                                                        self.result)

        if not len(self.result['agents']):
            raise CommException(CommError.COMMAND_RESULT_ERROR,
                                "No agents connected now: %s." % \
                                                        self.result)

        agents = []

        for agent in self.result['agents']:
            if 'microsoft' in agent['os-version'].lower():
                agent['iswin'] = True
                agent['path'] = ntpath
            else:
                agent['iswin'] = False
                agent['path'] = posixpath

            required = ['os-version',
                        'install-dir']
            for item in required:
                if not item in agent:
                    raise CommException(CommError.COMMAND_RESULT_ERROR,
                        "Missing required key '%s' in '%s'" % \
                                                    (item, str(agent)))


            if self.spec_str == 'type' and self.spec_val == 'all':
                agents.append(agent)
                continue

            if (self.spec_str == 'displayname' and agent['displayname'] == \
                                                    self.spec_val) \
                or (self.spec_str == "uuid" and \
                                        agent['uuid'] == self.spec_val) \
                or (self.spec_str == 'type' and agent['agent-type'] == \
                                                            self.spec_val):

                agents.append(agent)

        if agents:
            return agents

        raise CommException(CommError.COMMAND_RESULT_ERROR,
                            "Agent not found: %s %s" % \
                                        (self.spec_str, self.spec_val))

class CommHandlerApp(CommBase):
    def __init__(self, app):
        super(CommHandlerApp, self).__init__()

        self.app = app
        self.port = config.store.getint("palette", "telnet_port", default=9000)
        self.hostname = config.store.get("palette", "telnet_hostname",
                                         default="localhost")


class CommHandlerArgs(CommBase):
    # pylint: disable=too-many-instance-attributes
    def __init__(self):

        super(CommHandlerArgs, self).__init__()

        self.parser = argparse.ArgumentParser(sys.argv[0])

        # These are required for all:
        self.parser.add_argument('--hostname', dest='hostname',
                                 default='localhost')
        self.parser.add_argument('--port', dest='port', type=int, default=9000)
        self.parser.add_argument('--envid', dest='envid', type=int, default=1)

        self.parser.add_argument('-v', '--verbose', dest='verbose', type=int,
                                 default=1)

        group2 = self.parser.add_mutually_exclusive_group()
        group2.add_argument('--type', dest='agent_type', default='primary')
        group2.add_argument('--displayname', dest='displayname')
        group2.add_argument('--uuid', dest='uuid')

    def parse_args(self):

        self.args = self.parser.parse_args()

        self.hostname = self.args.hostname
        self.port = self.args.port
        self.envid = self.args.envid

        self.verbose = self.args.verbose

        self.preamble = "/envid=%d" % (self.envid)

        if self.args.displayname:
            self.preamble += ' /displayname="%s"' % (self.args.displayname)
            self.spec_str = "displayname"
            self.spec_val = self.args.displayname
        elif self.args.uuid:
            self.preamble += ' /uuid=%s' % (self.args.uuid)
            self.spec_str = "uuid"
            self.spec_val = self.args.uuid
        elif self.args.agent_type:
            self.spec_str = "type"
            self.spec_val = self.args.agent_type

            if self.spec_val != 'all':
                self.preamble += ' /type=%s' % (self.args.agent_type)

    def set_preamble(self, agent=None):
        if agent == None:
            self.preamble = ""
        self.preamble = "/envid=%d /uuid=%s" % (agent['envid'], agent['uuid'])

class CommHandlerCmd(CommHandlerArgs):
    def __init__(self):
        super(CommHandlerCmd, self).__init__()

        self.parse_args()
        self.verbose = 1
