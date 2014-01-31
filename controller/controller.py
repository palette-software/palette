#!/usr/bin/env python

import sys
import SocketServer as socketserver
import logging

from agent import AgentManager
import json
import time
import platform

from request import *
from inits import *
from exc import *
from httplib import HTTPException

from backup import BackupEntry, BackupManager
import sqlalchemy
import meta

version="0.1"

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
        print "body = ", body
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

        if body.has_key('error'):
            print >> self.wfile, body['error']
            print >> self.wfile, 'body:', body
            return

        if body.has_key("run-status"):
            print >> self.wfile, 'status:', body['run-status']

        if body.has_key("exit-status"):
            print >> self.wfile, 'exit-status:', body['exit-status']

        if body.has_key('stdout'):
            print >> self.wfile, body['stdout']

        if body.has_key('stderr'):
            if len(body['stderr']):
                print >> self.wfile, 'stderr:', body['stderr']

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
        if platform.system() == 'Windows':
            # Windows with Tableau uses port 8060
            url = "postgresql://palette:palpass:8060@localhost/paldb"
        else:
            url = "postgresql://palette:palpass@localhost/paldb"

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

        try:
            body = self._send_cli(command, target)
        except StandardError, e:
            return self.error("_send_cli failed with: " + str(e))

        if body.has_key('error'):
            return body

        body = self._get_status("cli", body['xid'])
        if body.has_key('error'):
            return body

        if not body.has_key("stdout"):
            return self.error("check status of cli failed - missing 'stdout' in reply", body)

        try:
            cleanup_dict = server._send_cleanup("cli", body['xid'])
        except StandardError, e:
            return self.error("cleanup cli failed with: " +  str(e))

        if cleanup_dict.has_key('error'):
            return cleanup_dict

        return body

    def _send_cli(self, cli_command, target=AGENT_TYPE_PRIMARY):
        """Send a "cli" command to an Agent.
            Returns a body with the results.
            Called without the agent manager lock."""

        self.log.debug("_send_cli")
        manager.lock()
        aconn = manager.agent_handle(target)
        if not aconn:
            manager.unlock()
            return self.error("Agent of this type not connected currently: %s" % target)

        req = Cli_Start_Request(cli_command)

        headers = {"Content-Type": "application/json"}

        self.log.debug('about to do the cli command, xid %d, command %s', req.xid, cli_command)
        try:
            aconn.httpconn.request('POST', '/cli', req.send_body, headers)
        except HTTPException, e:
            manager.unlock()
            return self.error("POST /cli failed with: " + str(e))
            
        self.log.debug('sent cli command.')
        try:
            res = aconn.httpconn.getresponse()
        except HTTPException, e:
            manager.unlock()
            return self.error("POST /cli getresponse failed with: " + str(e))

        self.log.debug('command: cli: ' + str(res.status) + ' ' + str(res.reason))

        if res.status != 200:
            manager.unlock()
            raise HttpException(res.status)

#        print "headers:", res.getheaders()
        self.log.debug("_send_cli reading...")
        body_json = res.read()
        manager.unlock()
        self.log.debug("_send_cli done reading, body_json: " + body_json)
        body = json.loads(body_json)
        if body == None:
            return self.error("POST /cli response had a null body")
        self.log.debug("_send_cli body:" + str(body))
        if not body.has_key('xid'):
            return self.error("POST /cli response was missing the xid", body)
        if req.xid != body['xid']:
            return self.error("POST /cli xid expected: %d but was %d" % (req.xid, body['xid']), body)

        if not body.has_key('run-status'):
            return self.error("POST /cli response missing 'run-status'", body)
        if body['run-status'] != 'running':
            return self.error("POST /cli response for 'run-status' was not 'running'", body)

        return body

    def _send_cleanup(self, command, xid, target=AGENT_TYPE_PRIMARY):
        """Send a "cleanup" command to an Agent.
            On success, returns the body of the reply.
            On failure, throws an exception.

            Called without the agent manager lock."""

        self.log.debug("_send_cleanup")
        manager.lock()
        aconn = manager.agent_handle(target)
        if not aconn:
            manager.unlock()
            return self.error("Agent of this type not connected currently: " + target)

        req = Cleanup_Request(xid)
        headers = {"Content-Type": "application/json"}
        self.log.debug('about to send the cleanup command, xid %d',  xid)
        try:
            aconn.httpconn.request('POST', '/%s' % command, req.send_body, headers)
        except HTTPException, e:
            manager.unlock()
            return self.error("POST /%s failed with: %s" % (command, str(e)))

        self.log.debug('sent cleanup command')
        try:
            res = aconn.httpconn.getresponse()
        except HTTPException, e:
            manager.unlock()
            return self.error("POST /%s getresponse failed with: %s" % (command, str(e)))

        self.log.debug('command: cleanup: ' + str(res.status) + ' ' + str(res.reason))

        if res.status != 200:
            manager.unlock()
            raise HttpException(res.status, res.reason)

        # Fixme: throw exception on http error
        self.log.debug("headers: " + str(res.getheaders()))
        self.log.debug("_send_cleanup reading...")
        body_json = res.read()
        manager.unlock()
        self.log.debug("done reading...")
        body = json.loads(body_json)
        if body == None:
            return self.error("Post /%s getresponse returned a null body" % command)
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

        req = Copy_Start_Request(body)

        headers = {"Content-Type": "application/json"}
        self.log.debug("sending copy command: " + str(body))
        try:
            target_conn.httpconn.request('POST', '/copy', req.send_body, headers)
        except HTTPException, e:
            return self.error("POST /copy failed with: " + str(e))

        self.log.debug("sent copy command.")

        try:
            res = target_conn.httpconn.getresponse()
            req.rec_status = res.status
        except HttpException, e:
            req.rec_status = e.status_code

        if req.rec_status != 200:
            manager.unlock()
            return self.error("Copy request failed with return status: %d" % res.status)

        try:
            body_json = res.read()
        except StandardError, e:
            manager.unlock()
            return self.error("Copy request read failed: " + str(e))

        manager.unlock()

        try:
            body = json.loads(body_json)
        except StandardError, e:
            return self.error("Copy request returned bad json: " + str(e))

        if body == None:
            return self.error("Copy request returned a null body")

        if not body.has_key('xid'):
            return self.error("Copy response was missing the xid", body)

        if body['xid'] != req.xid:
            return self.error("Copy response xid expected: %d but was %d" % (req.xid, body['xid']))

        body = server._get_status("copy", body['xid'])
        if body.has_key('error'):
            return body

        if not body.has_key("stdout"):
            return self.error("get status of copy failed.", body)

        try:
            cleanup_body = server._send_cleanup("copy", body['xid'])
        except HttpException, e:
            return self.error("cleanup cli failed with status %d", e.status_code)

        if cleanup_body.has_key('error'):
            return cleanup_body

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

            # fixme: lock (though copy_cmd also locks).

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
        if body.has_key('error'):
            return body

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
            self.log.debug("-----about to get status of command %s, xid %d", command, xid)
            aconn = manager.agent_handle(target)
            if not aconn:
                return self.error("Agent of this type not connected currently: %s" % target)

            manager.lock()
            uri = "/%s?xid=%d" % (command, xid)
            headers = {"Content-Type": "application/json"}

            self.log.debug("Sending GET " + uri)
            try:
                aconn.httpconn.request("GET", uri, None, headers)
            except HTTPException, e:
                manager.unlock()
                return self.error("GET %s failed with: " % (uri, str(e)))

            self.log.debug("Getting response from GET " +  uri)

            try:
                res = aconn.httpconn.getresponse()
            except (StandardError, HTTPException) as e:
                manager.unlock()
                return self.error("GET %s failed with: %s" % (uri, str(e)))

            self.log.debug("status: " + str(res.status) + ' ' + str(res.reason))
            if res.status != 200:
                manager.unlock()
                return self.error("GET %s command failed with: %s" % (uri, str(e)))
            self.log.debug("_get_status reading....")
            try:
                body_json = res.read()
            except StandardError, e:
                manager.unlock()
                return self.error("Get %s read body failed with: %s" % (uri, str(e)))

            try:
                body = json.loads(body_json)
            except StandardError, e:
                manager.unlock()
                return self.error("Get %s json bad, failed with: %s" % (uri, str(e)))
            if body == None:
                return self.error("Get /%s getresponse returned a null body" % uri)
            manager.unlock()
            self.log.debug("body = " + str(body))
            if not body.has_key('run-status'):
                return self.error("GET %S command reply was missing 'run-status'!  Will not retry." % (uri), body)
                break

            if body['run-status'] == 'finished':
                return body
            elif body['run-status'] == 'running':
                time.sleep(CLI_GET_STATUS_INTERVAL)
                continue
            else:
                return self.error("Unknown run-status: %s.  Will not retry." % body['run-status'], body)

    def error(self, msg, return_dict={}):
        """Returns error dictionary in standard format.  If passed
           a return_dict, then adds to it, otherwise a new return_dict
           is created."""

        return_dict['error'] = msg
        return return_dict

if __name__ == '__main__':
    import argparse
    import logger
    
    parser = argparse.ArgumentParser(description='Palette Controller')
    parser.add_argument('--debug', action='store_true', default=True)
    args = parser.parse_args()

    default_loglevel = logging.DEBUG    # fixme: change default to logging.INFO
    if args.debug:
        default_loglevel = logging.DEBUG

    log = logger.config_logging(MAIN_LOGGER_NAME, default_loglevel)

    log.info("Controller version: %s", version)

    log.debug("Starting agent listener.")

    global manager  # fixme: get rid of this global.
    manager = AgentManager()
    manager.log = log   # fixme
    manager.start()

    HOST, PORT = 'localhost', 9000
    server = Controller((HOST, PORT), CliHandler)
    server.log = log    # fixme
    server.serve_forever()
