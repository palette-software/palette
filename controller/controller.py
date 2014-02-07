#!/usr/bin/env python

import sys
import os
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

import sqlalchemy
import meta

from backup import BackupManager
from state import StateManager
from status import StatusMonitor

version="0.1"

global manager # fixme
global server # fixme
global log # fixme

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

        # Check to see if we're in a state to backup
        stateman = StateManager()
        states = stateman.get_states()

        if states[STATE_TYPE_MAIN] != STATE_MAIN_STARTED:
            print >> self.wfile, "FAIL: Can't backup - main state is:", states[STATE_TYPE_MAIN]
            log.debug("Can't backup - main state is: %s", states[STATE_TYPE_MAIN])
            return
        if states[STATE_TYPE_SECOND] != STATE_SECOND_NONE:
            print >> self.wfile, "FAIL: Can't backup - second state is:", states[STATE_TYPE_SECOND]
            log.debug("Can't backup - second state is: %s", states[STATE_TYPE_SECOND])
            return

        log.debug("-----------------Starting Backup-------------------")
            
        # fixme: lock to ensure against two simultaneous backups?
        stateman.update(STATE_TYPE_SECOND, STATE_SECOND_BACKUP)

        print >> self.wfile, "OK"
            
        body = server.backup_cmd()
        stateman.update(STATE_TYPE_SECOND, STATE_SECOND_NONE)
        self.report_status(body)

    def do_restore(self, argv):
        """Restore.  If the file/path we are restoring from is on a different
        machine than the Primary Agent, then get the file/path to the
        Primary Agent first."""

        if len(argv) != 1:
            print >> self.wfile, '[ERROR] usage: restore source-hostname:pathname'
            return

        # Check to see if we're in a state to restore
        stateman = StateManager()
        states = stateman.get_states()
        if states[STATE_TYPE_MAIN] != STATE_MAIN_STARTED and \
            states[STATE_TYPE_MAIN] != STATE_MAIN_STOPPED:
            print >> self.wfile, "FAIL: Can't backup - main state is:", states[STATE_TYPE_MAIN]
            log.debug("Can't restore - main state is: %s", states[STATE_TYPE_MAIN])
            return

        if states[STATE_TYPE_SECOND] != STATE_SECOND_NONE:
            print >> self.wfile, "FAIL: Can't restore - second state is:", states[STATE_TYPE_SECOND]
            log.debug("Can't restore - second state is: %s", states[STATE_TYPE_SECOND])
            return

        log.debug("-----------------Starting Restore-------------------")
            
        # fixme: lock to ensure against two simultaneous restores?
        stateman.update(STATE_TYPE_SECOND, STATE_SECOND_RESTORE)

        print >> self.wfile, "OK"
            
        body = server.restore_cmd(argv[0])

        stateman.update(STATE_TYPE_SECOND, STATE_SECOND_NONE)
        self.report_status(body)

    def do_copy(self, argv):
        """Copy a file from one agent to another."""
        if len(argv) != 2:
            print >> self.wfile, '[ERROR] Usage: copy source-agent-name:/filename dest-agent-name'
            return

        body = server.copy_cmd(argv[0], argv[1])
        self.report_status(body)

    def do_cli(self, argv):
        if not len(argv):
            self.error("'cli' requries an argument.")
            return

        cli_command = ' '.join(argv)
        body = server.cli_cmd(cli_command)
        self.report_status(body)

    def do_start(self, argv):
        if len(argv) != 0:
            print >> self.wfile, '[ERROR] usage: start'
            return
        
        # Check to see if we're in a state to start
        stateman = StateManager()
        states = stateman.get_states()
        if states[STATE_TYPE_MAIN] != 'stopped':
            # Even "Unknown" is not an okay state for starting as it
            # could mean the primary agent probably isn't connected.
            print >> self.wfile, "FAIL: Can't start - main state is:", states[STATE_TYPE_MAIN]
            log.debug("FAIL: Can't start - main state is: %s", states[STATE_TYPE_MAIN])
            return
        
        if states[STATE_TYPE_SECOND] != STATE_SECOND_NONE:
            print >> self.wfile, "FAIL: Can't start - second state is:", states[STATE_TYPE_SECOND]
            log.debug("FAIL: Can't start - second state is: %s", states[STATE_TYPE_SECOND])
            return
            
        stateman.update(STATE_TYPE_MAIN, STATE_MAIN_STARTING)

        log.debug("-----------------Starting Tableau-------------------")
        # fixme: Reply with "OK" only after the agent received the command?
        print >> self.wfile, "OK"

        body = server.cli_cmd('tabadmin start')

        # STARTED is set by the status monitor since it really knows the status.

        # fixme: check & report status to see if it really started?
        self.report_status(body)
    def do_stop(self, argv):
        if len(argv) != 0:
            print >> self.wfile, '[ERROR] usage: stop'
            return

        # Check to see if we're in a state to stop
        stateman = StateManager()
        states = stateman.get_states()
        if states[STATE_TYPE_MAIN] != STATE_MAIN_STARTED:
            log.debug("FAIL: Can't stop - main state is: %s", states[STATE_TYPE_MAIN])
            print >> self.wfile, "FAIL: Can't stop - current state is:", states[STATE_TYPE_MAIN]
            return

        # fixme: Prevent stopping if the use is doing a backup or restore?
        # fixme: Reply with "OK" only after the agent received the command?
        print >> self.wfile, "OK"

        stateman.update(STATE_TYPE_MAIN, STATE_MAIN_STOPPING)
        log.debug("-----------------Stopping Tableau-------------------")
        body = server.cli_cmd('tabadmin stop')

        # STOPPED is set by the status monitor since it really knows the status.

        # fixme: check & report status to see if it really stopped?
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
            url = "postgresql://palette:palpass@localhost:8060/paldb"
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
        backup_path = DEFAULT_BACKUP_DIR + '\\' + backup_name
        # Example path: C:\Palette\Data\Jan27_162225
        body = self.cli_cmd("tabadmin backup %s" % backup_path)
        if body.has_key('error'):
            return body

        # If two agents are connected, copy the backup to the
        # non-primary agent and delete the backup from the primary.
        non_primary_conn = None

        agents = manager.all_agents()
        for key in agents:
            if agents[key].auth['type'] != AGENT_TYPE_PRIMARY:
                non_primary_conn = agents[key]
                break

        primary_conn = manager.agent_conn_by_type(AGENT_TYPE_PRIMARY)

        if non_primary_conn:
            # Copy the backup to a non-primary agent
            copy_body = self.copy_cmd(\
                "%s:%s" % (primary_conn.auth['hostname'], backup_name),
                non_primary_conn.auth['hostname'])

            if copy_body.has_key('error'):
                return copy_body

            # Remove the backup file from the primary
            remove_body = self.cli_cmd(["DEL %s" % source_pathname])
            if remove_body.has_key('error'):
                return remove_body

            backup_ip_address = non_primary_conn.auth['ip-address']

        else:
            # Backup file remains on the primary.
            backup_ip_address = primary_conn.auth['ip-address']

        # Save name of backup and ip address of the primary agent to the db.
        self.dbinit()    #fixme
        self.backup = BackupManager(self.engine)
        self.backup.add(backup_name, backup_ip_address)

        return body

    def status_cmd(self):
        return self.cli_cmd('tabadmin status -v')

    def cli_cmd(self, command, target=AGENT_TYPE_PRIMARY):
        """ 1) Sends the command (a string)
            2) Waits for status/completion.  Saves the body from the status.
            3) Sends cleanup.
            4) Returns body from the status.
        """

        aconn = manager.agent_conn_by_type(target)
        if not aconn:
            return self.error("Agent of this type not connected currently: %s" % target)
        try:
            body = self._send_cli(command, aconn)
        except EnvironmentError, e:
            return self.error("_send_cli failed with: " + str(e))
        except HttpException, e:
            return self.error("_send_cli HttPException: " + str(e))

        if body.has_key('error'):
            return body

        body = self._get_status("cli", body['xid'], aconn)

        if body.has_key('error'):
            return body

        if not body.has_key("stdout"):
            return self.error("check status of cli failed - missing 'stdout' in reply", body)

        try:
            cleanup_dict = self._send_cleanup("cli", body['xid'], aconn)
        except EnvironmentError, e:
            return self.error("cleanup cli failed with: " +  str(e))

        if cleanup_dict.has_key('error'):
            return cleanup_dict

        return body

    def _send_cli(self, cli_command, aconn):
        """Send a "cli" command to an Agent.
            Returns a body with the results.
            Called without the connection lock."""

        self.log.debug("_send_cli")

        aconn.lock()

        req = Cli_Start_Request(cli_command)

        headers = {"Content-Type": "application/json"}

        self.log.debug('about to do the cli command, xid: %d, command: %s', req.xid, cli_command)
        try:
            aconn.httpconn.request('POST', '/cli', req.send_body, headers)
            self.log.debug('sent cli command.')

            res = aconn.httpconn.getresponse()

            self.log.debug('command: cli: ' + str(res.status) + ' ' + str(res.reason))

            if res.status != 200:
                aconn.unlock()
                raise HttpException(res.status, res.reason)

            # print "headers:", res.getheaders()
            self.log.debug("_send_cli reading...")
            body_json = res.read()
        except HTTPException, e:
            self.remove_agent(aconn)    # bad agent
            return self.error("POST /cli failed with: " + str(e))
        finally:
            aconn.unlock()

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
        if body['run-status'] != 'running' and body['run-status'] != 'finished':
            # FIXME: could possibly be finished.
            return self.error("POST /cli response for 'run-status' was not 'running'", body)

        return body

    def _send_cleanup(self, command, xid, aconn):
        """Send a "cleanup" command to an Agent.
            On success, returns the body of the reply.
            On failure, throws an exception.

            Called without the connection lock."""

        self.log.debug("_send_cleanup")
        aconn.lock()
        self.log.debug("_send_cleanup got lock")

        req = Cleanup_Request(xid)
        headers = {"Content-Type": "application/json"}
        self.log.debug('about to send the cleanup command, xid %d',  xid)
        try:
            aconn.httpconn.request('POST', '/%s' % command, req.send_body, headers)
            self.log.debug('sent cleanup command')
            res = aconn.httpconn.getresponse()
            self.log.debug('command: cleanup: ' + str(res.status) + ' ' + str(res.reason))
            if res.status != 200:
                aconn.unlock()
                self.log.debug("POST %s failed with res.status != 200: %d, reason: %s", command, res.status, res.reason)
                raise HttpException(res.status, res.reason)

            self.log.debug("headers: " + str(res.getheaders()))
            self.log.debug("_send_cleanup reading...")
            body_json = res.read()
        except HTTPException, e:
            self.remove_agent(aconn)    # bad agent
            self.log.debug("POST %s failed with HTTPException: %s", command, str(e))
            return self.error("POST /%s failed with: %s" % (command, str(e)))
        finally:
            aconn.unlock()

        self.log.debug("done reading...")
        body = json.loads(body_json)
        if body == None:
            return self.error("Post /%s getresponse returned a null body" % command)
        return body

    def copy_cmd(self, source_path, dest_name):
        """Send a wget command and checks the status.
           copy source-hostname:/path/to/file dest-hostname
                       <source_path>          <dest-hostname>
           generates:
            c:/Palette/bin/wget.exe --output=file http://primary-ip:192.168.1.1/file
           and sends it as a cli command to agent:
                dest-name
           Returns the body dictionary from the status."""

        if not source_path.find(':'):
            return self.error("[ERROR] Missing ':' in source path:" % source_path)

        (source_hostname, source_path) = source_path.split(':',1)

        if len(source_hostname) == 0 or len(source_path) == 0 or \
                                                    source_path[0] != '/':
            return self.error("[ERROR] Invalid source specification.  Requires '/'")

        agents = manager.all_agents()
        source_ip = None
        dest_conn = None

        for key in agents:
            if agents[key].auth['hostname'] == source_hostname:
                source_ip = agents[key].auth['ip-address']
            if agents[key].auth['hostname'] == dest_name:
                dest_conn = agents[key]

        msg = ""
        # fixme: make sure the source isn't the same as the dest
        if not source_ip:
            msg = "Unknown source-hostname: %s. " % source_hostname 
        if not dest_conn:
            msg += "Unknown dest-hostname: %s." % dest_name

        if not source_ip or not dest_conn:
            return self.error(msg)

        WGET_BIN="c:/Palette/bin/wget.exe"
        target_filename = os.path.basename(source_path) # filename without directory

        command = "%s --output-document=%s http://%s:%s%s" % \
            (WGET_BIN, target_filename,
                source_ip, dest_conn.auth['listen-port'], source_path)

        #GET_DIR="c:/Palette/Data/" # Use this still?  Or is it implied?

        return self.cli_cmd(command)

    def restore_cmd(self, arg):
        """Do a tabadmin restore of the passed arg, except
           the arg is in the format:
                source-hostname:pathname
            If the pathname is not on the Primary Agent, then copy
            it to the Primary Agent before doing the tabadmin restore
            Returns a body with the results/status.
        """

        stateman = StateManager()
        orig_states = stateman.get_states()
        if orig_states[STATE_TYPE_MAIN] == STATE_MAIN_STARTED:
            # Restore can run only when tableau is stopped.
            stateman.update(STATE_TYPE_MAIN, STATE_MAIN_STOPPING)
            log.debug("--------------Stopping Tableau for restore---------------")
            stop_body = self.cli_cmd("tabadmin stop")
            if stop_body.has_key('error'):
                self.info.debug("Restore: tabadmin stop failed")
                return stop_body

            # Give the status thread a bit of time to update the state to
            # STOPPED.
            stopped = False
            for i in range(3):
                states = stateman.get_states()
                if states[STATE_TYPE_MAIN] == STATE_MAIN_STOPPED:
                    stopped = True
                    self.log.debug("Restore: Tableau has stopped")
                    break
                self.log.debug("Restore: Tableau has not yet stopped")
                time.sleep(8)

            if not stopped:
                return self.error('[ERROR] Tableleau did not stop as requested.  Restore aborted.')

        # restore primary:c:\\stuff is possible (2 colons)
        # restore c:\stuff where "c:" is a disk, not a host.
        parts = arg.split(':', 1)

        source_hostname = parts[0]
        source_pathname = parts[1]

        if not os.path.isabs(source_pathname):
            # If it's not an absolute pathname, make it absolute, prepending
            # the default backup directory.
            source_pathname = DEFAULT_BACKUP_DIR + os.sep + source_pathname

        # Get the Primary Agent handle
        primary_conn = manager.agent_conn_by_type(AGENT_TYPE_PRIMARY)

        if not primary_conn:
            return self.error("[ERROR] No Primary Agent not connected.")

        # Check if the source_pathname is on the Primary Agent.
        if source_hostname != primary_conn.auth['hostname']:
            # The source_pathname isn't on the Primary agent:
            # We need to copy the file to the Primary.

            # copy_cmd arguments:
            #   source-agent-name:/filename
            #   dest-agent-hostname
            self.log.debug("Sending copy command: %s, %s", arg, primary_conn.auth['hostname'])
            body = server.copy_cmd(arg, primary_conn.auth['hostname'])

            if body.has_key("error"):
                return body

        # The file/path is on the Primary Agent.
        try:
            cmd = "tabadmin restore %s.tsbak" % source_pathname
            self.log.debug("restore sending command: %s", cmd)
            body = self.cli_cmd(cmd)
            if body.has_key('error'):
                return body
        except HTTPException, e:
            return self.error("HTTP Exception: " + str(e))

        # fixme: Do we need to add restore information to database?  
        # fixme: check status before cleanup? Or cleanup anyway?

        if source_hostname != primary_conn.auth['hostname']:
            # If the file was copied to the Primary Agent, delete
            # the temporary backup file we copied to the Primary Agent.
            self.log.debug("------------Restore: Removing file '%s' after restore------" % source_pathname)
            remove_body = self.cli_cmd(["DEL %s" % source_pathname])
            if remove_body.has_key('error'):
                return remove_body

        if orig_states[STATE_TYPE_MAIN] == STATE_MAIN_STARTED:
            # If Tableau was running before the restore, start it back up.
            self.log.debug("------------Restore: Starting tableau after restore------")
            stateman.update(STATE_TYPE_MAIN, STATE_MAIN_STARTING)
            start_body = self.cli_cmd("tabadmin start")
            if start_body.has_key('error'):
                self.info.debug("Restore: tabadmin start failed")
                return start_body

        return body

    def _get_status(self, command, xid, aconn):
        """Gets status on the command and xid.  Returns:
            Body in json with status/results.

            Note: Do not call this with the agent lock since
            we keep requesting status until the command is
            finished and that could be a long time.
        """
            
        status = False

#        debug for testing agent disconnects
#        print "sleeping"
#        time.sleep(5)
#        print "awake"

        uri = "/%s?xid=%d" % (command, xid)
        headers = {"Content-Type": "application/json"}

        while True:
            self.log.debug("-----about to get status of command %s, xid %d", command, xid)

            aconn.lock()
            self.log.debug("Sending GET " + uri)

            try:
                aconn.httpconn.request("GET", uri, None, headers)

                self.log.debug("Getting response from GET " +  uri)
                res = aconn.httpconn.getresponse()
                self.log.debug("status: " + str(res.status) + ' ' + str(res.reason))
                if res.status != 200:
                    self.remove_agent(aconn)    # bad agent
                    aconn.unlock()
                    return self.error("GET %s command failed with: %s" % (uri, str(e)))
#                debug for testing agent disconnects
#                print "sleeping"
#                time.sleep(5)
#                print "awake"

                self.log.debug("_get_status reading....")
                body_json = res.read()

                body = json.loads(body_json)
                if body == None:
                    return self.error("Get /%s getresponse returned a null body" % uri)

                self.log.debug("body = " + str(body))
                if not body.has_key('run-status'):
                    self.remove_agent(aconn)    # bad agent
                    aconn.unlock()
                    return self.error("GET %S command reply was missing 'run-status'!  Will not retry." % (uri), body)
    
                if body['run-status'] == 'finished':
                    return body
                elif body['run-status'] == 'running':
                    time.sleep(CLI_GET_STATUS_INTERVAL)
                    continue
                else:
                    self.remove_agent(aconn)    # bad agent
                    aconn.unlock()
                    return self.error("Unknown run-status: %s.  Will not retry." % body['run-status'], body)
            except HTTPException, e:
                    self.remove_agent(aconn)    # bad agent
                    return self.error("GET %s failed with HTTPException: %s" % (uri, str(e)))
            except EnvironmentError, e:
                    self.remove_agent(aconn)    # bad agent
                    return self.error("GET %s failed with: %s" % (uri, str(e)))
            finally:
                aconn.unlock()
    

    def error(self, msg, return_dict={}):
        """Returns error dictionary in standard format.  If passed
           a return_dict, then adds to it, otherwise a new return_dict
           is created."""

        return_dict['error'] = msg
        return return_dict

    def remove_agent(self, aconn):
        manager.remove_agent(aconn)
        if not manager.agent_conn_by_type(AGENT_TYPE_PRIMARY):
            statusmon.remove_all_status()
            statusmon.session.commit()

def main():
    import argparse
    import logger
    
    global server   # fixme
    global log      # fixme
    global manager   # fixme
    global statusmon # fixme
    
    parser = argparse.ArgumentParser(description='Palette Controller')
    parser.add_argument('--debug', action='store_true', default=True)
    parser.add_argument('--nostatus', action='store_true', default=False)
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

    # Need to instantiate to initialize state and status tables,
    # even if we don't run the status thread.
    statusmon = StatusMonitor(server, manager)

    if not args.nostatus:
        log.debug("Starting status monitor.")
        statusmon.start()

    server.log = log    # fixme
    server.serve_forever()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print "\nInterrupted.  Exiting."
        os._exit(1)
