#!/usr/bin/env python

import sys
import os
import SocketServer as socketserver
import logging

from agent import AgentManager
import json
import time

import ConfigParser as configparser

from request import *
from inits import *
from exc import *
from httplib import HTTPException

import sqlalchemy
from sqlalchemy.orm import sessionmaker
import meta

from backup import BackupManager
from state import StateManager
from status import StatusMonitor
from alert import Alert
from config import Config

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
        stateman = self.server.stateman
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

        alert = Alert(self.server.config, log)
        alert.send("Backup Started")

        print >> self.wfile, "OK"
            
        body = server.backup_cmd()
        stateman.update(STATE_TYPE_SECOND, STATE_SECOND_NONE)

        if not body.has_key('error'):
            alert.send("Backup Finished")
        else:
            alert.send("Backup failure: " + str(body['error']))
        self.report_status(body)

    def do_restore(self, argv):
        """Restore.  If the file/path we are restoring from is on a different
        machine than the Primary Agent, then get the file/path to the
        Primary Agent first."""

        if len(argv) != 1:
            print >> self.wfile, '[ERROR] usage: restore source-ip-address:pathname'
            return

        # Check to see if we're in a state to restore
        stateman = self.server.stateman
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
        # The "restore started" alert is done in restore_cmd(),
        # only after some sanity checking is done.
        alert = Alert(self.server.config, log)
        if not body.has_key('error'):
            alert.send("Restore Finished")
        else:
            alert.send("Restore failure: " + str(body['error']))

        self.report_status(body)

    def do_copy(self, argv):
        """Copy a file from one agent to another."""
        if len(argv) != 2:
            print >> self.wfile, '[ERROR] Usage: copy source-agent-name:filename dest-agent-name'
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
        stateman = self.server.stateman
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

        # Stop the maintenance web server and relinquish the web
        # server port before tabadmin start tries to listen on the web
        # server port.
        maint_body = server.maint("stop")
        if maint_body.has_key("error"):
            print >> self.wfile, "maint stop failed: " + str(maint_body)
            # let it continue ?

        body = server.cli_cmd('tabadmin start')

        # STARTED is set by the status monitor since it really knows the status.

        # fixme: check & report status to see if it really started?
        self.report_status(body)

    def do_stop(self, argv):
        if len(argv) != 0:
            print >> self.wfile, '[ERROR] usage: stop'
            return

        # Check to see if we're in a state to stop
        stateman = self.server.stateman
        states = stateman.get_states()
        if states[STATE_TYPE_MAIN] != STATE_MAIN_STARTED:
            log.debug("FAIL: Can't stop - main state is: %s", states[STATE_TYPE_MAIN])
            print >> self.wfile, "FAIL: Can't stop - current state is:", states[STATE_TYPE_MAIN]
            return

        # fixme: Prevent stopping if the user is doing a backup or restore?
        # fixme: Reply with "OK" only after the agent received the command?
        print >> self.wfile, "OK"

        stateman.update(STATE_TYPE_MAIN, STATE_MAIN_STOPPING)
        log.debug("-----------------Stopping Tableau-------------------")
        body = server.cli_cmd('tabadmin stop')
        if not body.has_key("error"):
            # Start the maintenance server only after Tableau has stopped
            # and reqlinquished the web server port.
            maint_body = server.maint("start")
            if maint_body.has_key("error"):
                print >> self.wfile, "maint start failed: " + str(maint_body)

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

    def do_maint(self, argv):
        if len(argv) != 1 or (argv[0] != "start" and argv[0] != "stop"):
            print >> self.wfile, '[ERROR] usage: maint start|stop'
            return

        body = server.maint(argv[0])
        if body:
            self.report_status(body)
        else:
            print >> self.wfile, "Done"

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
                "%s:%s.tsbak" % (primary_conn.auth['hostname'], backup_name),
                non_primary_conn.auth['hostname'])

            if copy_body.has_key('error'):
                return copy_body

            # Remove the backup file from the primary
            remove_body = self.cli_cmd(["DEL %s.tsbak" % backup_name])
            if remove_body.has_key('error'):
                return remove_body

            backup_ip_address = non_primary_conn.auth['ip-address']
            backup_hostname = non_primary_conn.auth['hostname']

        else:
            # Backup file remains on the primary.
            backup_ip_address = primary_conn.auth['ip-address']
            backup_hostname = primary_conn.auth['hostname']

        # Save name of backup, hostname ip address of the primary agent to the db.
        # fixme: create one of these per server.
        self.backup = BackupManager()
        self.backup.add(backup_name, primary_conn.uuid)

        return body

    def status_cmd(self):
        return self.cli_cmd('tabadmin status -v')

    def cli_cmd(self, command, aconn=None):
        """ 1) Sends the command (a string)
            2) Waits for status/completion.  Saves the body from the status.
            3) Sends cleanup.
            4) Returns body from the status.
        """

        if not aconn:
            aconn = manager.agent_conn_by_type(AGENT_TYPE_PRIMARY)
            if not aconn:
                return self.error("Agent of this type not connected currently: %s" % AGENT_TYPE_PRIMARY)
        try:
            body = self._send_cli(command, aconn)
        except EnvironmentError, e:
            return self.error("_send_cli failed with: " + str(e))
        except HttpException, e:
            return self.error("_send_cli HttPException: " + str(e))

        if body.has_key('error'):
            return body

        if not body.has_key('run-status'):
            return self.error("_send_cli body missing 'run-status: '" + str(e))

        # It is possible for the command to finish immediately.
        if body['run-status'] == 'finished':
            if body.has_key('stderr') and len(body['stderr']) and \
                                                        body['exit-status'] == 0:
                self.log.info("exit-status was 0 but stderr wasn't empty.")
                body['exit-status'] = 1 # Force error for exit-status.
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

        self.log.debug('about to do the cli command to %s, xid: %d, command: %s', \
                        aconn.auth['hostname'], req.xid, cli_command)
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
            self.log.debug("_send_cleanup unlocked")
            aconn.unlock()

        self.log.debug("done reading...")
        body = json.loads(body_json)
        if body == None:
            return self.error("Post /%s getresponse returned a null body" % command)
        return body

    def copy_cmd(self, source_path, dest_name):
        """Send a gget command and checks the status.
           copy source-hostname:/path/to/file dest-hostname
                       <source_path>          <dest-hostname>
           generates:
            c:/Palette/bin/pget.exe http://primary-ip:192.168.1.1/file dir/
           and sends it as a cli command to agent:
                dest-name
           Returns the body dictionary from the status."""

        if not source_path.find(':'):
            return self.error("[ERROR] Missing ':' in source path:" % source_path)

        (source_hostname, source_path) = source_path.split(':',1)

        if len(source_hostname) == 0 or len(source_path) == 0:
            return self.error("[ERROR] Invalid source specification.")

        agents = manager.all_agents()
        src = dst = None

        for key in agents:
            if agents[key].auth['hostname'] == source_hostname:
                src = agents[key]
            if agents[key].auth['hostname'] == dest_name:
                dst = agents[key]

        msg = ""
        # fixme: make sure the source isn't the same as the dest
        if not src:
            msg = "Unknown source-hostname: %s. " % source_hostname 
        if not dst:
            msg += "Unknown dest-hostname: %s." % dest_name

        if not src or not dst:
            return self.error(msg)

        PGET_BIN="c:/Palette/bin/pget.exe"

        source_ip = src.auth['ip-address']

        if 'install-dir' in dst.auth:
            target_dir = dst.auth['install-dir'] + "/Data/" 
        else:
            target_dir = 'c:/Palette/Data/'

        command = "%s http://%s:%s/%s %s" % \
            (PGET_BIN, source_ip, src.auth['listen-port'],
             source_path, target_dir)

        return self.cli_cmd(command, dst) # Send command to destination agent

    def restore_cmd(self, arg):
        """Do a tabadmin restore of the passed arg, except
           the arg is in the format:
                source-hostname:pathname
            If the pathname is not on the Primary Agent, then copy
            it to the Primary Agent before doing the tabadmin restore
            Returns a body with the results/status.
        """

        # Before we do anything, first do sanity checks.
        parts = arg.split(':')
        if len(parts) != 2:
            return self.error('[ERROR] Need exactly one colon in argument: ' + arg)

        source_hostname = parts[0]
        source_filename = parts[1]

        if os.path.isabs(source_filename):
            return self.error("[ERROR] May not specify an absolute pathname or disk: " + source_filename)

        source_fullpathname = DEFAULT_BACKUP_DIR + '\\' + source_filename + ".tsbak"

        # Get the Primary Agent handle
        primary_conn = manager.agent_conn_by_type(AGENT_TYPE_PRIMARY)

        if not primary_conn:
            return self.error("[ERROR] No Primary Agent not connected.")

        alert = Alert(self.config, log)
        alert.send("Restore Started")

        stateman = server.stateman
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

        # Check if the source_filename is on the Primary Agent.
        if source_hostname != primary_conn.auth['hostname']:
            # The source_filename isn't on the Primary agent:
            # We need to copy the file to the Primary.

            # copy_cmd arguments:
            #   source-agent-name:/filename
            #   dest-agent-hostname
            arg_tsbak = arg + ".tsbak"
            self.log.debug("Sending copy command: %s, %s", arg_tsbak, primary_conn.auth['hostname'])
            body = server.copy_cmd(arg_tsbak, primary_conn.auth['hostname'])

            if body.has_key("error"):
                self.log.debug("Copy failed with: " + str(body))
                return body

        # The file is now on the Primary Agent.

        # 'tabadmin restore ...' starts tableau as part of the restore procedure.
        # fixme: Maybe the maintenance web server wasn't running?
        maint_body = server.maint("stop")
        if maint_body.has_key("error"):
            self.info.debug("Restore: maint stop failed")
            # continue on..

        stateman.update(STATE_TYPE_MAIN, STATE_MAIN_STARTING)
        try:
            cmd = "tabadmin restore %s" % source_fullpathname
            self.log.debug("restore sending command: %s", cmd)
            body = self.cli_cmd(cmd)
        except HTTPException, e:
            return self.error("HTTP Exception: " + str(e))

        if body.has_key('error'):
            return body

        # fixme: Do we need to add restore information to database?  
        # fixme: check status before cleanup? Or cleanup anyway?

        if source_hostname != primary_conn.auth['hostname']:
            # If the file was copied to the Primary Agent, delete
            # the temporary backup file we copied to the Primary Agent.
            self.log.debug("------------Restore: Removing file '%s' after restore------" % source_fullpathname)
            remove_body = self.cli_cmd("DEL %s" % source_fullpathname)
            if remove_body.has_key('error'):
                return remove_body

        # On a successful restore, tableau starts itself.
        # fixme: The restore command usually still runs a while longer,
        # even after restore completes successfully.  Maybe note this in the UI?
        # So the "second" status stays at "restore" for a while after
        # tableau has started and the UI say "RUNNING".

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
                aconn.unlock()

                body = json.loads(body_json)
                if body == None:
                    return self.error("Get /%s getresponse returned a null body" % uri)

                self.log.debug("body = " + str(body))
                if not body.has_key('run-status'):
                    self.remove_agent(aconn)    # bad agent
                    return self.error("GET %S command reply was missing 'run-status'!  Will not retry." % (uri), body)
    
                if body['run-status'] == 'finished':
                    if body.has_key('stderr') and len(body['stderr']) and \
                                                        body['exit-status'] == 0:
                        self.log.info("exit-status was 0 but stderr wasn't empty.")
                        body['exit-status'] = 1 # Force error for exit-status.
                    return body
                elif body['run-status'] == 'running':
                    time.sleep(self.cli_get_status_interval)
                    continue
                else:
                    self.remove_agent(aconn)    # bad agent
                    return self.error("Unknown run-status: %s.  Will not retry." % body['run-status'], body)
            except HTTPException, e:
                    self.remove_agent(aconn)    # bad agent
                    return self.error("GET %s failed with HTTPException: %s" % (uri, str(e)))
            except EnvironmentError, e:
                    self.remove_agent(aconn)    # bad agent
                    return self.error("GET %s failed with: %s" % (uri, str(e)))
    

    def maint(self, action):
        # Get the Primary Agent handle
        aconn = manager.agent_conn_by_type(AGENT_TYPE_PRIMARY)

        if not aconn:
            return self.error("[ERROR] maint: No Primary Agent is connected.")

        send_body = json.dumps({"action": action})

        headers = {"Content-Type": "application/json"}

        aconn.lock()
        try:
            aconn.httpconn.request("POST", "/maint", send_body, headers)
            res = aconn.httpconn.getresponse()

            body_json = res.read()
            if body_json:
                body = json.loads(body_json)
                self.log.debug("maint reply = " + str(body))
            else:
                body = {}
                self.log.debug("maint reply empty.")

        except EnvironmentError, e:
            return self.error("maint failed with: " + str(e))
        except HttpException, e:
            return self.error("maint HttPException: " + str(e))
        finally:
            aconn.unlock()

        return body

    def error(self, msg, return_dict={}):
        """Returns error dictionary in standard format.  If passed
           a return_dict, then adds to it, otherwise a new return_dict
           is created."""

        return_dict['error'] = msg
        return return_dict

    def remove_agent(self, aconn):
        manager.remove_agent(aconn)
        if not manager.agent_conn_by_type(AGENT_TYPE_PRIMARY):
            # fixme: why get Session() from here?
            session = statusmon.Session()
            statusmon.remove_all_status(session)
            session.commit()

def main():
    import argparse
    import logger
    
    global server   # fixme
    global log      # fixme
    global manager   # fixme
    global statusmon # fixme
 
    parser = argparse.ArgumentParser(description='Palette Controller')
    parser.add_argument('config', nargs='?', default=None)
    parser.add_argument('--debug', action='store_true', default=True)
    parser.add_argument('--nostatus', action='store_true', default=False)
    args = parser.parse_args()

    config = Config(args.config)
    host = config.getdef('controller', 'host', 'localhost');
    port = config.getintdef('controller', 'port', 9000);

    default_loglevel = logging.DEBUG    # fixme: change default to logging.INFO
    if args.debug:
        default_loglevel = logging.DEBUG

    log = logger.config_logging(MAIN_LOGGER_NAME, default_loglevel)

    log.info("Controller version: %s", version)

    # engine is once per single application process.
    # see http://docs.sqlalchemy.org/en/rel_0_9/core/connections.html
    meta.engine = sqlalchemy.create_engine(meta.url, echo=False)
    # Create the table definition ONCE, before all the other threads start.
    meta.Base.metadata.create_all(bind=meta.engine)

    log.debug("Starting agent listener.")

    global manager  # fixme: get rid of this global.
    manager = AgentManager(config)
    manager.log = log   # fixme
    manager.start()

    server = Controller((host, port), CliHandler)
    server.config = config
    server.cli_get_status_interval = config.getdef('controller', 'cli_get_status_interval', 10)

    # Need to instantiate to initialize state and status tables,
    # even if we don't run the status thread.
    statusmon = StatusMonitor(server, manager)
    server.statusmon = statusmon

    if not args.nostatus:
        log.debug("Starting status monitor.")
        statusmon.start()

    server.stateman = StateManager(config, log)

    server.log = log    # fixme
    server.serve_forever()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print "\nInterrupted.  Exiting."
        os._exit(1)
