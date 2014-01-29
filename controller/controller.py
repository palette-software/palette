#!/usr/bin/env python

import sys
import SocketServer as socketserver

from agent import AgentManager
import json
import time

from request import *
from inits import *

from backup import BackupEntry, BackupManager
import sqlalchemy
import meta

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

        body = server.cli_cmd("tabadmin status -v")
        self.report_status(body)

    def do_backup(self, argv):
        if len(argv):
            print >> self.wfile, '[ERROR] backup does not have an argument.'
            return
        body = server.backup_cmd()
        self.report_status(body)

    def do_restore(self, argv):
        """Restore.  If the file/path we are restoring from is on a different
        machine than the Primary Agent, then copy the file/path to the
        Primary Agent first."""

        if len(argv) != 1:
            print >> self.wfile, '[ERROR] usage: restore [source-hostname]:pathname'
            return
        
        body = server.restore_cmd(argv[0])
        self.report_status(body)

    def do_copy(self, argv):
        """copy a file from the source to the target."""
        if len(argv) != 4:
            print >> self.wfile, '[ERROR] Usage: copy source-hostname source-path target-hostname target-path'
            return

        body = server.copy_cmd(argv[0], argv[1], argv[2], argv[3])
        self.report_status(body)

    def do_cli(self, argv):
        if not len(argv):
            self.error("'cli' requries an argument.")
            return

        cli_command = ' '.join(argv)
        body = server.cli_cmd(cli_command)
        self.report_status(body)

    def report_status(self, body):
        """Passed an HTTP body and prints info about it back to the user."""

        if body.has_key("status"):
            if body['status'] == 'success':
                print >> self.wfile, 'Success.'
                if body.has_key('stdout'):
                    print >> self.wfile, body['stdout']
                return
            elif body['status'] == 'failure':
                print >> self.wfile, 'failure.'

                if body.has_key('error'):
                    print >> self.wfile, body['error']
                if body.has_key('stdout'):
                    print >> self.wfile, 'stdout:', body['stdout']
                if body.has_key('stderr'):
                    if len(body['stderr']):
                        print >> self.wfile, 'stderr:', body['stderr']
            else:
                print >> self.wfile, "Error, invalid status.  body returned:", body
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

    def dbinit(self):
        # fixme: move ...

        # fixme: move to .ini config file
        url = "postgresql://palette:palpass@localhost/paldb"
        echo = False

        self.engine = sqlalchemy.create_engine(url, echo=False)

        # fixme: Do only once...
        meta.Base.metadata.create_all(bind=self.engine)

    def backup_cmd(self):
        """Does a backup."""
        # fixme: make sure another backup isn't already running?
        # fixme: Do we want to specify the directory for the backup?
        # If not, the backup is saved in the server bin directory.
        backup_name = time.strftime("%b%d_%H%M%S")
        # Example name: Jan27_162225
        body = self.cli_cmd("tabadmin backup %s" % backup_name )
        if body.has_key('error'):
            return body

        # fixme: add backup information to database
        primary_agent = manager.agent_handle(AGENT_TYPE_PRIMARY)
        # Save name of backup and ip address of the primary agent to the db.
        ip_address = primary_agent.auth['ip-address']

        self.dbinit()    #fixme
        self.backup = BackupManager(self.engine)
        self.backup.add(backup_name, ip_address)

        return body

    def cli_cmd(self, command, target=AGENT_TYPE_PRIMARY):
        """ 1) Sends the command (a string)
            2) Waits for status/completion.  Saves the body from the status.
            3) Sends cleanup.
            4) Returns body from the status.
        """
        manager.lock()
        body = self._send_cli(command, target)
        manager.unlock()

        if body.has_key('error'):
            return body

        body = self._get_status("cli", body['xid'])
        if not body.has_key("stdout"):
            return self.error("check status of cli failed", body)  #fixme: more info

        manager.lock()
        try:
            cleanup_dict = server._send_cleanup("cli", body['xid'])
        except HttpException, e:
            manager.unlock()
            return self.error("cleanup cli failed with status %d", e.status_code)

        manager.unlock()
        return body

    def _send_cli(self, cli_command, target=AGENT_TYPE_PRIMARY):
        """Send a "cli" command to an Agent.
            Returns a body with the results."""

        print "_send_cli"
        aconn = manager.agent_handle(target)
        if not aconn:
            return self.error("Agent of this type not connected currently: %s" % target)

        req = Start_Cli_Request(cli_command)

        headers = {"Content-Type": "application/json"}

        print 'about to do the cli command, xid', req.xid,'command:', cli_command
        aconn.httpconn.request('POST', '/cli', req.send_body, headers)
        print 'did it'
        res = aconn.httpconn.getresponse()
        print 'command: cli: ' + str(res.status) + ' ' + str(res.reason)
        # fixme: check the correct xid is returned correct
        req.rec_status = res.status

        if res.status != 200:
            raise HttpException(res.status)

#        print "headers:", res.getheaders()
        print "reading..."
        body_json = res.read()
        print "done reading..."
        #fixme: test bad json, bad status, etc.
        try:
            body = json.loads(body_json)
        except:
            print "Bad json:", body_json
            raise HttpException(405)

        return body

    def _send_cleanup(self, command, xid, target=AGENT_TYPE_PRIMARY):
        """Send a "cleanup" command to an Agent.
            On success, returns the body of the reply.
            On failure, throws an exception."""

        print "_send_cleanup"
        aconn = manager.agent_handle(target)
        if not aconn:
            print "Agent of this type not connected currently:", target
            return 0    #fixme

        req = Cleanup_Request(xid)
        req.xid = xid
        headers = {"Content-Type": "application/json"}
        print 'about to send the cleanup command, xid', xid
        aconn.httpconn.request('POST', '/%s' % command, req.send_body, headers)
        print 'sent cleanup command'
        res = aconn.httpconn.getresponse()
        print 'command: cleanup: ' + str(res.status) + ' ' + str(res.reason)
        req.rec_status = res.status

        if res.status != 200:
            raise HttpException(res.status)

        # Fixme: throw exception on http error
        print "headers:", res.getheaders()
        print "reading..."
        body_json = res.read()
        print "done reading..."
        body = json.loads(body_json)
        return body

    def copy_cmd(self, source_hostname, source_path, target_hostname, target_path):
        """Sends a copy command and checks the status.
            Returns the body dictionary from the status."""

        manager.lock()

        agents = manager.all_agents()
        source_ip = None
        target_conn = None

        for key in agents:
            if agents[key].auth['hostname'] == source_hostname:
                source_ip = agents[key].auth['ip-address']
            if agents[key].auth['hostname'] == target_hostname:
                target_conn = agents[key]

        msg = ""
        # fixme: make sure the source isn't the same as the target
        if not source_ip:
            msg = "Unknown source-hostname: %s.  " % source_hostname 
        if not target_conn:
            msg += "Unknown target-hostname: %s." % target_hostname

        if not source_ip or not target_conn:
            manager.unlock()
            return self.error(msg)

        # Tell:
        #   1) V1: The source that the target will be requesting a file.
        #   2) The target to get the source path
        body = { "source": source_ip,
                 "source-filename": source_path,
                 "target": target_conn.auth["ip-address"],
                 "target-path": target_path
                }

        req = Start_Copy_Request(body)

        headers = {"Content-Type": "application/json"}
        print "sending copy command:", body
        target_conn.httpconn.request('POST', '/copy', req.send_body, headers)

        try:
            res = target_conn.httpconn.getresponse()
            req.rec_status = res.status
        except HttpException, e:
            req.rec_status = e.status_code

        if req.rec_status != 200:
            return self.error("Copy request failed with return status: %d" % res.status)

        # Fixme: throw exception on http error
        body_json = res.read()
        body = json.loads(body_json)

        manager.unlock()

        # fixme: check for xid...

        body = server._get_status("copy", body['xid'])
        if not body.has_key("stdout"):
            return self.error("check status of copy failed")   #fixme: more info

        manager.lock()
        try:
            status = server._send_cleanup("copy", body['xid'])
        except HttpException, e:
            manager.unlock()
            return self.error("cleanup cli failed with status %d", e.status_code)

        manager.unlock()
        return body

    def restore_cmd(self, arg):
        """Do a tabadmin restore of the passed arg, except
           the arg is in the format:
                source-hostname:pathname
            If the pathname is not on the Primary Agent, then copy
            it to the Primary Agent before doing the tabadmin restore
            Returns a body with the results/status."""
           
        if ':' in arg:
            # The user specified a source-hostname.
            parts = arg.split(':')
            if len(parts) != 2:
                return self.error('[ERROR] Too many colons in argument:' % arg)

            source_hostname = parts[0]
            source_pathname = parts[1]

            # Get the Primary Agent handle
            primary_agent = manager.agent_handle(AGENT_TYPE_PRIMARY)

            if not primary_agent:
                return self.error("[ERROR] Not Primary Agent not connected.")

            # Check if the source_pathname is on the Primary Agent.
            if source_hostname != primary_agent.auth['hostname']:
                # The source_pathname isn't on the Primary agent:
                # We need to copy the file to the Primary.

                # fixme: change target path to something we set on the primary
                # like a tmp filename.
                target_pathname = source_pathname

                body = server.copy_cmd(source_hostname, source_pathname, \
                    primary_agent.auth['hostname'], target_pathname)

                if body.has_key("error"):
                    return body
        else:
            source_pathname = arg

        # The file/path is on the Primary Agent.
        body = self.cli_cmd("tabadmin restore %s" % source_pathname)
        # fixme: Do we need to add restore information to database?  

        # fixme: check status before cleanup? Or cleanup anyway?

        if ':' in arg and source_hostname != primary_agent.auth['hostname']:
            # If the file was copied to the Primary Agent, delete
            # the temporary backup file we copied to the Primary Agent.
            remove_body = self.cli_cmd(["DEL %s" % target_pathname])
            if remove_body.has_key('error'):
                return remove_body

        return body

    def _get_status(self, command, xid, target=AGENT_TYPE_PRIMARY):
        """Gets status on the command and xid.  Returns:
            Body in json with status/results.

            Note: Do not call this with the agent lock since
            we keep requesting status until the command is
            finished and that could be a long time.
        """
            
        status = False

        while True:
            print "about to get status of command", command, "xid", xid
            aconn = manager.agent_handle(target)
            if not aconn:
                return self.error("Agent of this type not connected currently: %s" % target)

            manager.lock()
            uri = "/%s?xid=%d" % (command, xid)
            headers = {"Content-Type": "application/json"}

            aconn.httpconn.request("GET", uri, None, headers)

            res = aconn.httpconn.getresponse()
            print "status:", str(res.status) + ' ' + str(res.reason)
            if res.status != 200:
                manager.unlock()
                return self.error("Command failed!")

            print "reading...."
            body_json = res.read()
            body = json.loads(body_json)
            manager.unlock()
            print "body = ", body
            if not body.has_key('run-status'):
                print "Reply was missing 'run-status'!  Will not retry."
                break

            if body['run-status'] == 'finished':
                return body
            elif body['run-status'] == 'running':
                time.sleep(CLI_GET_STATUS_INTERVAL)
                continue
            else:
                return self.error("Unknown run-status: %s.  Will not retry." % body['run-status'])

    def error(self, msg, return_dict={}):
        """Returns error dictionary in standard format.  If passed
           a return_dict, then adds to it, otherwise a new return_dict
           is created."""

        return_dict['error'] = msg
        return_dict['status'] = 'failure'
        return return_dict

class HttpException(Exception):
    def __init__(self, status_code):
        self.status_code = status_code

if __name__ == '__main__':
    
    global manager  # fixme: get rid of this global.

    manager = AgentManager()
    manager.start()

    HOST, PORT = 'localhost', 9000
    server = Controller((HOST, PORT), CliHandler)
    server.serve_forever()
