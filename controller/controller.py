#!/usr/bin/env python

import sys
import SocketServer as socketserver

from agent import AgentManager
import json
import time

from request import *
from inits import *

# How long to wait between getting cli status
CLI_GET_STATUS_INTERVAL=1

global manager # todo

class CliHandler(socketserver.StreamRequestHandler):

    def error(self, msg, *args):
        if args:
            msg = msg % args
        print >> self.wfile, '[ERROR] '+msg

    def do_status(self, argv):
        if len(argv):
            print >> self.wfile, '[ERROR] status does not have an argument.'
            return

        body = self.do_cli("tabadmin status -v")
        if body.has_key("stdout"):
            print >> self.wfile, "stdout:", body['stdout']
        if body.has_key("stderr"):
            print >> self.wfile, "stderr:", body['stderr']
        else:
            print >> self.wfile, "Error, body returned:", body

    def do_list(self, argv):
        if argv:
            self.error("'list' does not take any arguments")
            return
        print >> self.wfile, 'OK'

    def do_cli(self, argv):
        if not len(argv):
            self.error("'cli' requries an argument.")
            return

        manager.lock()
        body = server.send_cli(argv)
        manager.unlock()

        manager.lock()
        body = server.get_status("cli", body['xid'])
        manager.unlock()
        if not body.has_key("stdout"):
            print >> self.wfile, "check status of cli failed"   #fixme: more info
            return {}

        manager.lock()
        status = server.send_cleanup("cli", body['xid'])
        manager.unlock()
        if status != 200:
            print >> self.wfile, "cleanup cli failed with status:", status
            return {}

        return body


    def handle(self):
        while True:
            data = self.rfile.readline().strip()
            if not data: break

            argv = data.split()
            cmd = argv.pop(0)

            if not hasattr(self, 'do_'+cmd):
                self.error('invalid command: %s', cmd)
                continue

            f = getattr(self, 'do_'+cmd)
            f(argv)

class Controller(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

    def send_cli(self, argv, target=AGENT_TYPE_PRIMARY):
        """Send a "cli" command to an Agent.
            On success, returns True.
            On failure, returns False."""

        print "send_cli"
        aconn = manager.agent_handle(target)
        if not aconn:
            print "Agent of this type not connected currently:", target
            return False

        cli_command = ''.join(argv)
        req = Cli_Request("start", cli_command)

        headers = {"Content-Type": "application/json"}

        print 'about to do the cli command, xid', req.xid
        aconn.httpconn.request('POST', '/cli', req.send_body, headers)
        print 'did it'
        res = aconn.httpconn.getresponse()
        print 'command: cli: ' + str(res.status) + ' ' + str(res.reason)
        # fixme: check the correct xid is returned correct
        req.rec_status = res.status

        # Fixme: throw exception on http error
        body_json = res.read()
        body = json.loads(body_json)
        return body

    def send_cleanup(self, command, xid, target=AGENT_TYPE_PRIMARY):
        """Send a "cleanup" command to an Agent.
            On successful launch, returns the body of the reply.
            On failure, throws an exception."""

        print "send_cleanup"
        aconn = manager.agent_handle(target)
        if not aconn:
            print "Agent of this type not connected currently:", target
            return 0    #fixme

        req = Cli_Request("cleanup")
        req.xid = xid
        print 'about to send the cleanup command, xid', xid
        aconn.httpconn.request('POST', '/cli', req.send_body)
        print 'sent cleanup command'
        res = aconn.httpconn.getresponse()
        print 'command: cleanup: ' + str(res.status) + ' ' + str(res.reason)
        return res.status

    def get_status(self, command, xid, target=AGENT_TYPE_PRIMARY):
        """Gets status on the command and xid.  Returns:
            False on failure.
            Body in json on success.
        """
            
        status = False

        while True:
            time.sleep(CLI_GET_STATUS_INTERVAL)
            print "about to get status of command", command, "xid", xid
            aconn = manager.agent_handle(target)
            if not aconn:
                print "Agent of this type not connected currently:", target
                return False

            uri = "/%s?xid=%d" % (command, xid)
            aconn.httpconn.request("GET", uri)

            res = aconn.httpconn.getresponse()
            print "status:", str(res.status) + ' ' + str(res.reason)
            if res.status != 200:
                print "Command failed!"
                return False

            print "reading...."
            body_json = res.read()
            body = json.loads(body_json)
            print "body = ", body
            if not body.has_key('run-status'):
                print "Reply was missing 'run-status'!  Will not retry."
                break

            if body['run-status'] == 'finished':
                return body
            elif body['run-status'] == 'running':
                continue
            else:
                print "Unknown run-status:", body['run-status']," Will not retry."
                return False

if __name__ == '__main__':
    
    global manager  # fixme: get rid of this global.

    manager = AgentManager()
    manager.start()

    HOST, PORT = 'localhost', 9000
    server = Controller((HOST, PORT), CliHandler)
    server.serve_forever()
