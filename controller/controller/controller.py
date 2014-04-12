#!/usr/bin/env python

import sys
import os
import shlex
import SocketServer as socketserver
import socket

import json
import time

from request import *
from exc import *

import httplib
import inspect

import sqlalchemy
from sqlalchemy.orm import sessionmaker
import meta

from agentmanager import AgentManager
from backup import BackupManager
from state import StateManager, StateEntry
from status import StatusMonitor
from alert import Alert
from config import Config
from domain import Domain

from version import VERSION

global manager # fixme
global server # fixme
global log # fixme

class Command(object):

    def __init__(self, line):
        self.dict = {}
        self.name = None
        self.args = []

        for token in shlex.split(line):
            if token.startswith("/"):
                token = token[1:]
                L = token.split("=", 1)
                if len(L) > 1:
                    key = L[0].strip()
                    value = L[1].strip()
                else:
                    key = token.strip()
                    value = None
                self.dict[key] = value
            elif self.name == None:
                self.name = token
            else:
                self.args.append(token.strip())
            

class CliHandler(socketserver.StreamRequestHandler):

    SUCCESS = True
    FAIL = False

    def finish(self):
        """Overrides the StreamRequestHandler's finish().
           Handles exceptions more gracefully and
           makes sure telnet clients are closed.
        """

        if not self.wfile.closed:
            try:
                self.wfile.flush()
            except socket.error:
                # An final socket error may have occurred here, such as
                # the local error ECONNABORTED.
                pass

        try:
            self.wfile.close()
        except socket.error:
            pass

        self.rfile.close()

    def error(self, msg, *args):
        if args:
            msg = msg % args
        print >> self.wfile, '[ERROR] '+msg

    def print_client(self, format, *args):
        """
            Try to write format % args to self.wfile, which is
            the telnet client.
            If this fails, due to a telnet client already disconnected,
            send it to stdout.

            Why we need this method:
                If a print to ">> self.wfile" fails, and we didn't catch
                the exception, the do_*() method terminates, which is
                not good.  This method handles it by sending a failed
                print to ">> self.wfile" to sys.stdout.  Instead, we
                might want to just drop the bytes since the client has
                disconnected and doesn't really care.
        """

        line = format % args
        line += '\n'
        try:
            print  >> self.wfile, line
        except EnvironmentError:
            line += '[TELNET] ' + line
            sys.stdout.write(line)

    def do_help(self, cmd):
        for name, m in inspect.getmembers(self, predicate=inspect.ismethod):
            if name.startswith("do_"):
                print >> self.wfile, '  ' + name[3:]
                if m.__doc__:
                    print >> self.wfile, '    ' + m.__doc__
                if hasattr(m, '__usage__'):
                    print >> self.wfile, '    usage: ' + m.__usage__

    def do_status(self, cmd):
        if len(cmd.args):
            print >> self.wfile, '[ERROR] status does not have an argument.'
            return

        aconn = self.get_aconn(cmd.dict)
        if not aconn:
            self.error('agent not found')
            return

        body = server.cli_cmd("tabadmin status -v", aconn)
        self.report_status(body)
    do_status.__usage__ = 'status'

    def do_backup(self, cmd):
        """
            Returns:
                CliHandler.SUCCESS on success and
                CliHandler.FAIL on failure.
        """

        target = None
        if len(cmd.args) > 1:
            print >> self.wfile, '[ERROR] usage: backup [<target_displayname>]'
            return CliHandler.FAIL
        elif len(cmd.args) == 1:
            target = cmd.args[0]

        aconn = self.get_aconn(cmd.dict)
        if not aconn:
            self.error('agent not found')
            return CliHandler.FAIL

        # Check to see if we're in a state to backup
        stateman = self.server.stateman
        states = stateman.get_states()

        # Backups can be done when Tableau is either started or stopped.
        if states[StateEntry.STATE_TYPE_MAIN] not in \
          (StateEntry.STATE_MAIN_STARTED, StateEntry.STATE_MAIN_STOPPED):
            print >> self.wfile, "FAIL: Can't backup - main state is:", \
              states[StateEntry.STATE_TYPE_MAIN]
            log.debug("Can't backup - main state is: %s", \
              states[StateEntry.STATE_TYPE_MAIN])
            return CliHandler.FAIL
        if states[StateEntry.STATE_TYPE_BACKUP] != StateEntry.STATE_BACKUP_NONE:
            print >> self.wfile, "FAIL: Can't backup - backup state is:", \
              states[StateEntry.STATE_TYPE_BACKUP]
            log.debug("Can't backup - backup state is: %s", \
              states[StateEntry.STATE_TYPE_BACKUP])
            return CliHandler.FAIL

        log.debug("-----------------Starting Backup-------------------")
            
        # fixme: lock to ensure against two simultaneous backups?
        stateman.update(StateEntry.STATE_TYPE_BACKUP, \
          StateEntry.STATE_BACKUP_BACKUP)

        alert = Alert(self.server.config, log)
        alert.send("Backup Started")

        print >> self.wfile, "OK"

        body = server.backup_cmd(aconn, target)
        stateman.update(StateEntry.STATE_TYPE_BACKUP, \
          StateEntry.STATE_BACKUP_NONE)

        self.report_status(body)
        if not body.has_key('error'):
            alert.send("Backup Finished", body)
            return CliHandler.SUCCESS
        else:
            alert.send("Backup Failed", body)
            return CliHandler.FAIL

    def do_restore(self, cmd):
        """Restore.  If the file/path we are restoring from is on a different
        machine than the Primary Agent, then get the file/path to the
        Primary Agent first."""

        if len(cmd.args) != 1:
            print >> self.wfile, \
              '[ERROR] usage: restore source-ip-address:pathname'
            return
        target = cmd.args[0]

        aconn = self.get_aconn(cmd.dict)
        if not aconn:
            self.error('agent not found')
            return

        # Check to see if we're in a state to restore
        stateman = self.server.stateman
        states = stateman.get_states()
        if states[StateEntry.STATE_TYPE_MAIN] != StateEntry.STATE_MAIN_STARTED and \
            states[StateEntry.STATE_TYPE_MAIN] != StateEntry.STATE_MAIN_STOPPED:
            print >> self.wfile, "FAIL: Can't backup - main state is:", \
              states[StateEntry.STATE_TYPE_MAIN]
            log.debug("Can't restore - main state is: %s", \
              states[StateEntry.STATE_TYPE_MAIN])
            return

        if states[StateEntry.STATE_TYPE_BACKUP] != \
              StateEntry.STATE_BACKUP_NONE:
            print >> self.wfile, "FAIL: Can't restore - backup state is:", \
              states[StateEntry.STATE_TYPE_BACKUP]
            log.debug("Can't restore - backup state is: %s", \
              states[StateEntry.STATE_TYPE_BACKUP])
            return

        # Do a backup before we try to do a restore.
        #FIXME: refactor do_backup() into do_backup() and backup()
        backup_success = self.do_backup(Command(""))

        if not backup_success:
            self.print_client("Backup failed.  Will still try to restore.")

        log.debug("-----------------Starting Restore-------------------")
            
        # fixme: lock to ensure against two simultaneous restores?
        stateman.update(StateEntry.STATE_TYPE_BACKUP, StateEntry.STATE_BACKUP_RESTORE1)
        self.print_client("OK")
            
        body = server.restore_cmd(aconn, target)

        stateman.update(StateEntry.STATE_TYPE_BACKUP, StateEntry.STATE_BACKUP_NONE)
        # The "restore started" alert is done in restore_cmd(),
        # only after some sanity checking is done.
        alert = Alert(self.server.config, log)
        if not body.has_key('error'):
            alert.send("Restore Finished", body)
        else:
            alert.send("Restore Failed" , body)

        self.report_status(body)

    def do_copy(self, cmd):
        """Copy a file from one agent to another."""

        if len(cmd.args) != 2:
            self.error(self.do_copy.__doc__)
            return

        body = server.copy_cmd(cmd.args[0], cmd.args[1])
        self.report_status(body)
    do_copy.__usage__ = 'copy source-agent-name:filename dest-agent-name'

    def do_list(self, cmd):
        """List information about all connected agents."""

        if len(cmd.args):
            self.error("Usage: list")
            return

        agents = manager.all_agents()

        if len(agents) == 0:
            print >> self.wfile, "No agents connected."
            return

        for key in agents:
            print >> self.wfile, "\t", agents[key].displayname, "(displayname)"
            print >> self.wfile, "\t\ttype:", agents[key].auth['type']
            print >> self.wfile, "\t\tip-address:", agents[key].auth['ip-address']
            print >> self.wfile, "\t\tlisten-port:", agents[key].auth['listen-port']
            print >> self.wfile, "\t\thostname:", agents[key].auth['hostname']
            print >> self.wfile, "\t\tuuid:", agents[key].auth['uuid']
    do_list.__usage__ = 'list'

    def do_cli(self, cmd):
        if len(cmd.args) < 1:
            print >> self.wfile, "[ERROR] usage: cli [ { /displayname=dname | /hostname=hname | /uuid=uuidname | /type={primary|worker|other} } ] command"
            return

        aconn = self.get_aconn(cmd.dict)
        if not aconn:
            self.error('agent not found')
            return

        cli_command = ' '.join(cmd.args)
        print >> self.wfile, "Sending to displayname '%s' (type: %s):" % \
          (aconn.displayname, aconn.auth['type'])
        print >> self.wfile, cli_command

        body = server.cli_cmd(cli_command, aconn)
        self.report_status(body)

    def do_pget(self, cmd):
        if len(cms.args) < 2:
            self.error(self.do_pget.__usage__)
            return

        aconn = self.get_aconn(cmd.dict)
        if not aconn:
            self.error('agent not found')
            return

        pget_cmd = Controller.PGET_BIN
        for arg in cms.args:
            if ' ' in arg:
                pget_cmd += ' "' + arg + '"'
            else:
                pget_cmd += ' ' + arg
        if aconn:
            print >> self.wfile, "Sending to displayname '%s' (type: %s):" % \
                        (aconn.displayname, aconn.auth['type'])
        else:
            print >> self.wfile, "Sending:",

        print >> self.wfile, pget_cmd
        body = server.cli_cmd(pget_cmd, aconn)
        self.report_status(body)
    do_pget.__usage__ = 'pget [ { /displayname=dname | /hostname=hname | /uuid=uuidname | /type={primary|worker|other} } ] https://...... local-name'

    def do_ping(self, argv, aconn=None):
        if len(argv):
            print >> self.wfile, '[ERROR] Usage: ping [ { /displayname=dname | /hostname=hname | /uuid=uuidname | /type={primary|worker|other} } ]'
            return

        if aconn and type(aconn) == type([]):
            self.error("Invalid request: More than one agent was selected: %d",
                                                                    len(aconn))
            return

        if aconn:
            print >> self.wfile, "Sending ping to displayname '%s' (type: %s)." % \
                        (aconn.displayname, aconn.auth['type'])
        else:
            print >> self.wfile, "Sending ping."

        body = server.ping_immediate(aconn)
        self.report_status(body)

    def do_start(self, cmd):
        if len(cmd.args) != 0:
            print >> self.wfile, '[ERROR] usage: start'
            return

        aconn = self.get_aconn(cmd.dict)
        if not aconn:
            self.error('agent not found')
            return
        
        # Check to see if we're in a state to start
        stateman = self.server.stateman
        states = stateman.get_states()
        if states[StateEntry.STATE_TYPE_MAIN] != 'stopped':
            # Even "Unknown" is not an okay state for starting as it
            # could mean the primary agent probably isn't connected.
            print >> self.wfile, "FAIL: Can't start - main state is:", \
              states[StateEntry.STATE_TYPE_MAIN]
            log.debug("FAIL: Can't start - main state is: %s", \
              states[StateEntry.STATE_TYPE_MAIN])
            return
        
        if states[StateEntry.STATE_TYPE_BACKUP] != \
              StateEntry.STATE_BACKUP_NONE:
            print >> self.wfile, "FAIL: Can't start - backup state is:", \
              states[StateEntry.STATE_TYPE_BACKUP]
            log.debug("FAIL: Can't start - backup state is: %s", \
              states[StateEntry.STATE_TYPE_BACKUP])
            return
            
        stateman.update(StateEntry.STATE_TYPE_MAIN, \
              StateEntry.STATE_MAIN_STARTING)

        log.debug("-----------------Starting Tableau-------------------")
        # fixme: Reply with "OK" only after the agent received the command?
        print >> self.wfile, "OK"

        # Stop the maintenance web server and relinquish the web
        # server port before tabadmin start tries to listen on the web
        # server port.
        maint_body = server.maint("stop")
        if maint_body.has_key("error"):
            self.print_client("maint stop failed: " + str(maint_body))
            # let it continue ?

        body = server.cli_cmd('tabadmin start', aconn)
        if body.has_key("exit-status"):
            exit_status = body['exit-status']
        else:
            exit_status = 1 # if no 'exit-status' then consider it failed.

        if exit_status:
            # The "tableau start" failed.  Go back to "STOPPED" state.
            alert = Alert(server.config, log)
            alert.send("Could not start tableau", body)
            stateman.update(StateEntry.STATE_TYPE_MAIN, StateEntry.STATE_MAIN_STOPPED)
        # STARTED is set by the status monitor since it really knows the status.

        self.report_status(body)

    def do_stop(self, cmd):
        if len(cmd.args) != 0:
            print >> self.wfile, '[ERROR] usage: stop'
            return

        aconn = self.get_aconn(cmd.dict)
        if not aconn:
            self.error('agent not found')
            return

        # Check to see if we're in a state to stop
        stateman = self.server.stateman
        states = stateman.get_states()
        if states[StateEntry.STATE_TYPE_MAIN] != StateEntry.STATE_MAIN_STARTED:
            log.debug("FAIL: Can't stop - main state is: %s", states[StateEntry.STATE_TYPE_MAIN])
            print >> self.wfile, "FAIL: Can't stop - current state is:", states[StateEntry.STATE_TYPE_MAIN]
            return

        #FIXME: refactor do_backup() into do_backup() and backup()
        backup_success = self.do_backup(Command(""))

        if not backup_success:
            self.print_client("Backup failed.  Will not attempt stop.")
            return

        # Note: Make sure to set the state in the database before
        # we report "OK" back to the client since "OK" to the UI client
        # results in an immediate check of the state.
        stateman.update(StateEntry.STATE_TYPE_MAIN, StateEntry.STATE_MAIN_STOPPING)

        log.debug("-----------------Stopping Tableau-------------------")
        # fixme: Prevent stopping if the user is doing a backup or restore?
        # fixme: Reply with "OK" only after the agent received the command?
        self.print_client("OK")

        body = server.cli_cmd('tabadmin stop', aconn)
        if not body.has_key("error"):
            # Start the maintenance server only after Tableau has stopped
            # and reqlinquished the web server port.
            maint_body = server.maint("start")
            if maint_body.has_key("error"):
                self.print_client("maint start failed: " + str(maint_body))

        # STOPPED is set by the status monitor since it really knows the status.

        # fixme: check & report status to see if it really stopped?
        self.report_status(body)

    def report_status(self, body):
        """Passed an HTTP body and prints info about it back to the user."""

        if body.has_key('error'):
            self.print_client(body['error'])
            self.print_client('body: %s', body)
            return

        if body.has_key("run-status"):
            self.print_client('run-status: %s', body['run-status'])

        if body.has_key("exit-status"):
            self.print_client('exit-status: %d', body['exit-status'])

        if body.has_key('stdout'):
            self.print_client(body['stdout'])

        if body.has_key('stderr'):
            if len(body['stderr']):
                self.print_client('stderr: %s', body['stderr'])

    def do_maint(self, cmd):
        """usage: maint [start|stop]"""

        if len(cmd.args) != 1:
            self.error(self.do_maint.__doc__)
            return

        action = cmd.args[0]
        if action != "start" and action != "stop":
            self.error(self.do_maint.__doc__)
            return

        body = server.maint(action)
        if body:
            print >> self.wfile, 'body: ' + str(body)
        else:
            print >> self.wfile, "{}"

    def do_displayname(self, cmd):
        """Set the display name for an agent"""
        if len(cmd.args) != 2:
            print >> self.wfile, '[ERROR] Usage: displayname agent-hostname agent-displayname'
            return

        error = server.displayname_cmd(cmd.args[0], cmd.args[1])
        if error:
            self.error(error)
        else:
            print >> self.wfile, "OK"

    def do_nop(self, cmd):
        """usage: nop"""

        print >> self.wfile, "OK"

    def get_aconn(self, opts):
        # FIXME: This method is a temporary hack while we
        #        clean up the telnet commands

        aconn = None

        if opts.has_key('uuid'):
            val = opts['uuid']
            aconn = manager.agent_conn_by_uuid(val)
            if not aconn:
                self.error("No connected agent with uuid=%s", val)
        elif opts.has_key('type'):
            val = opts['type']
            aconn = manager.agent_conn_by_type(val)
            if not aconn:
                self.error("No connected agent with type=%s", val)
        elif opts.has_key('displayname'):
            val = opts['displayname']
            aconn = manager.agent_conn_by_displayname(val)
            if not aconn:
                self.error("No connected agent with displayname=%s", val)
        elif opts.has_key('hostname'):
            val = opts['hostname']
            aconn = manager.agent_conn_by_hostname(val)
            if not aconn:
                self.error("No connected agent with hostname=%s", val)
        else:
            aconn = manager.agent_conn_by_type(AgentManager.AGENT_TYPE_PRIMARY)
            if not aconn:
                self.error("No connected agent with type=%s", \
                  AgentManager.AGENT_TYPE_PRIMARY)

        return aconn

    def handle(self):
        while True:
            data = self.rfile.readline().strip()
            if not data: break

            cmd = Command(data)

            if not hasattr(self, 'do_'+cmd.name):
                self.error('invalid command: %s', cmd.name)
                continue

            # <command> /displayname=X /type=primary, /uuid=Y, /hostname=Z [args]
            f = getattr(self, 'do_'+cmd.name)
            f(cmd)

class Controller(socketserver.ThreadingMixIn, socketserver.TCPServer):

    LOGGER_NAME = "main"
    allow_reuse_address = True

    DEFAULT_BACKUP_DIR = AgentManager.DEFAULT_INSTALL_DIR + "Data\\"
    PGET_BIN = "pget.exe"

    def backup_cmd(self, aconn, target=None):
        """Does a backup."""
        # fixme: make sure another backup isn't already running?

        # Note: In a backup context 'target' is the destination for the backup,
        #       while in a restore context, 'target' is the source.

        # Example name: Jan27_162225.tsbak
        backup_name = time.strftime("%b%d_%H%M%S") + ".tsbak"

        primary_conn = \
          manager.agent_conn_by_type(AgentManager.AGENT_TYPE_PRIMARY)

        if 'install-dir' in primary_conn.auth:
            backup_path = primary_conn.auth['install-dir'] + "Data\\" + backup_name
        else:
            backup_path = self.DEFAULT_BACKUP_DIR + backup_name

        # Example path: c:\\Program\ Files\ (x86)\\Palette\\Data\\Jan27_162225.tsbak
        cmd = 'tabadmin backup \\\"%s\\\"' % backup_path
        body = self.cli_cmd(cmd, aconn)
        if body.has_key('error'):
            return body

        agents = manager.all_agents()

        non_primary_conn = None
        if target != None:
            for key in agents:
                if agents[key].displayname == target:
                    # FIXME: make sure agent is connected
                    if agents[key].auth['type'] != \
                      AgentManager.AGENT_TYPE_PRIMARY:
                        non_primary_conn = agents[key]
                    target = None # so we know we found the target
                    break
        else:
            for key in agents:
                if agents[key].auth['type'] != \
                  AgentManager.AGENT_TYPE_PRIMARY:
                    # FIXME: make sure agent is connected
                    # FIXME: ticket #218: When the UI supports selecting
                    #        a target, remove the code that automatically
                    #        selects a remote.
                    if non_primary_conn == None:
                        non_primary_conn = agents[key]
                    else:
                        if agents[key].displayname < \
                          non_primary_conn.displayname:
                            non_primary_conn = agents[key]
        if target:
            self.error("agent %s does not exist or is offline" % target)

        if non_primary_conn:
            backup_loc = non_primary_conn
            # Copy the backup to a non-primary agent
            copy_body = self.copy_cmd(\
                "%s:%s" % (primary_conn.displayname, backup_name),
                non_primary_conn.displayname)

            if copy_body.has_key('error'):
                msg = "Copy of backup file '%s' to agent '%s' failed.  Will leave the backup file on the primary agent. Error was: %s" % \
                    (backup_name, non_primary_conn.displayname, \
                                                        copy_body['error'])
                self.log.info(msg)
                body['info'] = msg
                # Something was wrong with the copy to the non-primary agent.
                #  Leave the backup on the primary after all.
                backup_loc = primary_conn
            else:
                # The copy succeeded.
                # Remove the backup file from the primary
                remove_cli = 'CMD /C DEL \\\"%s\\\"' % backup_path
                remove_body = self.cli_cmd(remove_cli, aconn)

                # Check if the DEL worked.
                if remove_body.has_key('error'):
                    body['info'] = "DEL of backup file failed after copy.  Command: '%s'. Error was: %s" % (remove_cli, remove_body['error'])
        else:
            backup_loc = primary_conn
            # Backup file remains on the primary.

        # Save name of backup, agentid to the db.
        # fixme: create one of these per server.
        self.backup = BackupManager(self.domainid)
        self.backup.add(backup_name, backup_loc.agentid)

        return body

    def status_cmd(self, aconn):
        return self.cli_cmd('tabadmin status -v', aconn)

    def cli_cmd(self, command, aconn):
        """ 1) Sends the command (a string)
            2) Waits for status/completion.  Saves the body from the status.
            3) Sends cleanup.
            4) Returns body from the status.
        """

        try:
            body = self._send_cli(command, aconn)
        except EnvironmentError, e:
            return self.error("_send_cli (%s) failed with: %s" % (command, str(e)))
        except HttpException, e:
            return self.error("_send_cli (%s) HttPException: %s" % (command, str(e)))

        if body.has_key('error'):
            return body

        if not body.has_key('run-status'):
            return self.error("_send_cli (%s) body response missing 'run-status: '" % \
                (command, str(e)))

        # It is possible for the command to finish immediately.
        if body['run-status'] == 'finished':
            return body

        cli_body = self._get_status("cli", body['xid'], aconn)

        if not cli_body.has_key("stdout"):
            self.log.error("check status of cli failed - missing 'stdout' in reply", cli_body)

        try:
            cleanup_body = self._send_cleanup("cli", body['xid'], aconn)
        except EnvironmentError, e:
            cleanup_body = { "error": "cleanup cli failed with: " +  str(e) }

        if cli_body.has_key("error"):
            return cli_body

        if cleanup_body.has_key('error'):
            return cleanup_body

        return cli_body

    def _send_cli(self, cli_command, aconn):
        """Send a "cli" command to an Agent.
            Returns a body with the results.
            Called without the connection lock."""

        self.log.debug("_send_cli")

        aconn.lock()

        req = CliStartRequest(cli_command)

        headers = {"Content-Type": "application/json"}

        self.log.debug("about to send the cli command to '%s', type '%s' xid: %d, command: %s", \
                aconn.displayname, aconn.auth['type'], req.xid, cli_command)
        try:
            aconn.httpconn.request('POST', '/cli', req.send_body, headers)
            self.log.debug('sent cli command.')

            res = aconn.httpconn.getresponse()

            self.log.debug('command: cli: ' + str(res.status) + ' ' + str(res.reason))

            if res.status != 200: # FIXME: use a define
                raise HttpException(res.status, res.reason)

            # print "headers:", res.getheaders()
            self.log.debug("_send_cli reading...")
            body_json = res.read()

        except (httplib.HTTPException, EnvironmentError) as e:
            self.remove_agent(aconn, "Communication lost with agent.")    # bad agent
            return self.error("POST /cli failed with: " + str(e))
        except:
            self.remove_agent(aconn, "Communication error with agent.")    # bad agent
            return self.error("POST /cli failed with unexpected error: " + str(sys.exc_info()[0]))
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

        req = CleanupRequest(xid)
        headers = {"Content-Type": "application/json"}
        self.log.debug('about to send the cleanup command, xid %d',  xid)
        try:
            aconn.httpconn.request('POST', '/%s' % command, req.send_body, headers)
            self.log.debug('sent cleanup command')
            res = aconn.httpconn.getresponse()
            self.log.debug('command: cleanup: ' + str(res.status) + ' ' + str(res.reason))
            if res.status != 200: # FIXME
                self.log.debug("POST %s failed with res.status != 200: %d, reason: %s, body: %s", \
                  command, res.status, res.reason, res.read())
                raise HttpException(res.status, res.reason)

            self.log.debug("headers: " + str(res.getheaders()))
            self.log.debug("_send_cleanup reading...")
            body_json = res.read()
        except HttpException, e:
            return self.error("_send_cleanup (%s) HttPException: %s" % (command, str(e)))
        except (httplib.HTTPException, EnvironmentError) as e:
            self.remove_agent(aconn, "Command to agent failed.")    # bad agent
            self.log.debug("POST %s failed with HTTPException: %s", command, str(e))
            return self.error("POST /%s failed with: %s" % (command, str(e)))
        finally:
            self.log.debug("_send_cleanup unlocked")
            # FIXME: cannot call aconn.unlock() after self.remove_agent()
            aconn.unlock()

        self.log.debug("done reading...")
        body = json.loads(body_json)
        if body == None:
            return self.error("Post /%s getresponse returned a null body" % command)
        return body

    def copy_cmd(self, source_path, dest_name):
        """Sends a pget command and checks the status.
           copy source-displayname:/path/to/file dest-displayname
                       <source_path>          <dest-displayname>
           generates:
               pget.exe https://primary-ip:192.168.1.1/file dir/
           and sends it as a cli command to agent:
                dest-displayname
           Returns the body dictionary from the status."""

        if source_path.find(':') == -1:
            return self.error("[ERROR] Missing ':' in source path: %s" % source_path)

        (source_displayname, source_path) = source_path.split(':',1)

        if len(source_displayname) == 0 or len(source_path) == 0:
            return self.error("[ERROR] Invalid source specification.")

        agents = manager.all_agents()
        src = dst = None

        for key in agents.keys():
            manager.lock()
            if not agents.has_key(key):
                self.log.info("copy_cmd: agent with conn_id '%d' is now gone and won't be checked." % key)
                manager.unlock()
                continue
            agent = agents[key]
            manager.unlock()

            if agent.displayname == source_displayname:
                src = agent
            if agent.displayname == dest_name:
                dst = agent

        msg = ""
        # fixme: make sure the source isn't the same as the dest
        if not src:
            msg = "No connected source agent with displayname: %s. " % \
              source_displayname 
        if not dst:
            msg += "No connected destination agent with displayname: %s." % \
              dest_name

        if not src or not dst:
            return self.error(msg)

        source_ip = src.auth['ip-address']

        if 'install-dir' in dst.auth:
            target_dir = dst.auth['install-dir'] + "Data"
        else:
            target_dir = self.DEFAULT_BACKUP_DIR

        command = '%s https://%s:%s/%s "%s"' % \
            (Controller.PGET_BIN, source_ip, src.auth['listen-port'],
             source_path, target_dir)

        copy_body = self.cli_cmd(command, dst) # Send command to destination agent
        return copy_body

    def restore_cmd(self, aconn, target):
        """Do a tabadmin restore of the passed target, except
           the target is in the format:
                source-displayname:pathname
            If the pathname is not on the Primary Agent, then copy
            it to the Primary Agent before doing the tabadmin restore
            Returns a body with the results/status.
        """

        # Note: In a restore context, 'target' is the source of the backup,
        #       while in a backup context 'target' is the destination.

        # Before we do anything, first do sanity checks.
        parts = target.split(':')
        if len(parts) != 2:
            return self.error('[ERROR] Need exactly one colon in argument: ' + target)

        source_displayname = parts[0]
        source_filename = parts[1]

        if os.path.isabs(source_filename):
            return self.error("[ERROR] May not specify an absolute pathname or disk: " + source_filename)

        # Get the Primary Agent handle
        primary_conn = manager.agent_conn_by_type(AgentManager.AGENT_TYPE_PRIMARY)

        if not primary_conn:
            return self.error("[ERROR] No Primary Agent is connected.")

        if 'install-dir' in primary_conn.auth:
            source_fullpathname = primary_conn.auth['install-dir'] + "Data\\" + source_filename
        else:
            source_fullpathname = self.DEFAULT_BACKUP_DIR + source_filename

        # Check if the source_filename is on the Primary Agent.
        if source_displayname != primary_conn.displayname:
            # The source_filename isn't on the Primary agent:
            # We need to copy the file to the Primary.

            # copy_cmd arguments:
            #   source-agent-name:/filename
            #   dest-agent-displayname
            self.log.debug("Restore: Sending copy command: %s, %s", target, primary_conn.displayname)
            body = server.copy_cmd(target, primary_conn.displayname)

            if body.has_key("error"):
                self.log.debug("Restore: Copy of backup file '%s' from '%s' failed.  Error was: %s " % \
                        (source_fullpathname, source_displayname, body['error']))
                return body

        # The restore file is now on the Primary Agent.

        alert = Alert(self.config, log)
        alert.send("Restore Started")

        stateman = server.stateman
        orig_states = stateman.get_states()
        if orig_states[StateEntry.STATE_TYPE_MAIN] == StateEntry.STATE_MAIN_STARTED:
            # Restore can run only when tableau is stopped.
            stateman.update(StateEntry.STATE_TYPE_MAIN, StateEntry.STATE_MAIN_STOPPING)
            log.debug("--------------Stopping Tableau for restore---------------")
            stop_body = self.cli_cmd("tabadmin stop", aconn)
            if stop_body.has_key('error'):
                self.log.info("Restore: tabadmin stop failed")
                if source_displayname != primary_conn.displayname:
                    # If the file was copied to the Primary, delete
                    # the temporary backup file we copied to the Primary.
                    self.delete_file(aconn, source_fullpathname)
                return stop_body

            # Give Tableau and the status thread a bit of time to stop
            # and update the state to STOPPED.
            stopped = False
            for i in range(15):
                states = stateman.get_states()
                if states[StateEntry.STATE_TYPE_MAIN] == StateEntry.STATE_MAIN_STOPPED:
                    stopped = True
                    self.log.debug("Restore: Tableau has stopped (on check %d)", i)
                    break
                self.log.debug("Restore: Check #%d: Tableau has not yet stopped", i)
                time.sleep(8)

            if not stopped:
                if source_displayname != primary_conn.displayname:
                    # If the file was copied to the Primary, delete
                    # the temporary backup file we copied to the Primary.
                    self.delete_file(aconn, source_fullpathname)
                return self.error('[ERROR] Tableleau did not stop as requested.  Restore aborted.')

        # 'tabadmin restore ...' starts tableau as part of the restore procedure.
        # fixme: Maybe the maintenance web server wasn't running?
        maint_body = server.maint("stop")
        if maint_body.has_key("error"):
            self.log.info("Restore: maint stop failed")
            # continue on, not a fatal error...
            restore_body['info'] = "Restore: maint stop failed.  Error was: %s" \
                % maint_body['error']

        stateman.update(StateEntry.STATE_TYPE_MAIN, StateEntry.STATE_MAIN_STARTING)
        stateman.update(StateEntry.STATE_TYPE_BACKUP, StateEntry.STATE_BACKUP_RESTORE2)
        try:
            cmd = 'tabadmin restore \\\"%s\\\"' % source_fullpathname
            self.log.debug("restore sending command: %s", cmd)
            restore_body = self.cli_cmd(cmd, aconn)
        except httplib.HTTPException, e:
            restore_body = { "error": "HTTP Exception: " + str(e) }

        if restore_body.has_key('error'):
            restore_success = False
        else:
            restore_success = True

        # fixme: Do we need to add restore information to the database?  
        # fixme: check status before cleanup? Or cleanup anyway?

        if source_displayname != primary_conn.displayname:
            # If the file was copied to the Primary, delete
            # the temporary backup file we copied to the Primary.
            self.delete_file(aconn, source_fullpathname)
            
        if not restore_success:
            # On a successful restore, tableau starts itself.
            # fixme: eventually control when tableau is started and
            # stopped, rather than have tableau automatically start
            # during the restore.
            self.log.info("Restore: starting tableau after failed restore.")
            start_body = self.cli_cmd("tabadmin start", aconn)
            if start_body.has_key('error'):
                self.log.info("Restore: 'tabadmin start' failed after failed restore.")
                msg = "Restore: 'tabadmin start' failed after failed restore.  Error was: %s" % start_body['error']
                if restore_body.has_key('info'):
                    restore_body['info'] += "\n" + msg
                else:
                    restore_body['info'] = msg

        return restore_body

    def delete_file(self, aconn, source_fullpathname):
        """Delete a file, check the error, and return the body result."""
        self.log.debug("Removing file '%s'" % source_fullpathname)
        cmd = 'CMD /C DEL \\\"%s\\\"' % source_fullpathname
        remove_body = self.cli_cmd(cmd, aconn)
        if remove_body.has_key('error'):
            self.log.info('DEL of "%s" failed.' % source_fullpathname)
            # fixme: report somewhere the DEL failed.
        return remove_body

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
            self.log.debug("about to get status of command %s, xid %d", command, xid)

            if not manager.agent_connected(aconn):
                self.log.info("Agent '%s' (type: '%s', conn_id %d) disconnected before finishing: %s" %
                    (aconn.displayname, aconn.auth['type'], aconn.conn_id, uri))
                return self.error("Agent '%s' (type: '%s', conn_id %d) disconnected before finishing: %s" %
                    (aconn.displayname, aconn.auth['type'], aconn.conn_id, uri))

            aconn.lock()
            self.log.debug("Sending GET " + uri)

            try:
                aconn.httpconn.request("GET", uri, None, headers)

                self.log.debug("Getting response from GET " +  uri)
                res = aconn.httpconn.getresponse()
                self.log.debug("status: " + str(res.status) + ' ' + str(res.reason))
                if res.status != 200: # FIXME
                    self.remove_agent(aconn, "Failed status from agent.")
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
                    self.remove_agent(aconn, "Agent returned invalid status.")
                    return self.error("GET %S command reply was missing 'run-status'!  Will not retry." % (uri), body)
    
                if body['run-status'] == 'finished':
                    # Make sure if the command failed, that the 'error'
                    # key is set.
                    if body['exit-status'] != 0:
                        if body.has_key('stderr'):
                            body['error'] = body['stderr']
                        else:
                            body['error'] = "Failed with exit status: %d" % body['exit-status']
                    return body
                elif body['run-status'] == 'running':
                    time.sleep(self.cli_get_status_interval)
                    continue
                else:
                    self.remove_agent(aconn, "Communication failure with agent:  Unknown run-status returned from agent: %s" % body['run-status'])    # bad agent
                    return self.error("Unknown run-status: %s.  Will not retry." % body['run-status'], body)
            except httplib.HTTPException, e:
                    self.remove_agent(aconn, "HTTP communication failure with agent: " + str(e))    # bad agent
                    return self.error("GET %s failed with HTTPException: %s" % (uri, str(e)))
            except EnvironmentError, e:
                    self.remove_agent(aconn, "Communication failure with agent. Unexpected error: " + \
                                                    str(e))    # bad agent
                    return self.error("GET %s failed with: %s" % (uri, str(e)))
    

    def maint(self, action):
        # Get the Primary Agent handle
        aconn = manager.agent_conn_by_type(AgentManager.AGENT_TYPE_PRIMARY)

        if not aconn:
            return self.error("[ERROR] maint: No Primary Agent is connected.")

        send_body = json.dumps({"action": action})

        headers = {"Content-Type": "application/json"}

        aconn.lock()
        body = {}
        try:
            aconn.httpconn.request("POST", "/maint", send_body, headers)
            res = aconn.httpconn.getresponse()

            rawbody = res.read()
            if res.status != httplib.OK:
                body = self.httperror(res, rawbody)
            elif rawbody:
                body = json.loads(rawbody)
                self.log.debug("maint reply = " + str(body))
            else:
                body = {}
                self.log.debug("maint reply empty.")

        except (httplib.HTTPException, EnvironmentError) as e:
            return self.error("maint failed: " + str(e))
            self.remove_agent(aconn, "Agent 'maint' command failed: " + str(e))    # bad agent
        finally:
            aconn.unlock()

        return body

    def ping_immediate(self, aconn):
        if not aconn:
            # Get the Primary Agent handle
            aconn = manager.agent_conn_by_type(AgentManager.AGENT_TYPE_PRIMARY)

        if not aconn:
            return self.error("[ERROR] ping: Agent not connected.")

        aconn.lock()
        self.log.debug("about to send a 'ping' to %s" % aconn.displayname)

        try:
            aconn.httpconn.request("POST", "/ping")
            res = aconn.httpconn.getresponse()

            self.log.debug("ping reply status = %d", res.status)
            ignore = res.read()
            if res.status == 200: #FIXME
                return {'stdout': "Ping to %s (type %s) succeeded with status %d." % \
                    (aconn.displayname, aconn.auth['type'], res.status) }

            self.remove_agent(aconn, "Communication failure with agent.  Status returned: %d" % res.status)    # bad agent
            return self.error("ping command to %s failed with status %d" % \
                                    (aconn.displayname, res.status))

        except (httplib.HTTPException, EnvironmentError) as e:
            return self.error("ping failed: " + str(e))
            self.remove_agent(aconn, "Communication failure with agent.  Error: " + str(e))    # bad agent
        finally:
            aconn.unlock()

        self.logger.log(logging.ERROR, "This line should not be reached!")
        return self.error("Should not have reached this line.")

    def displayname_cmd(self, hostname, displayname):
        """Sets displayname for the agent with the given hostname. At
           this point assumes hostname is unique in the database."""

        return manager.set_displayname(hostname, displayname)

    def error(self, msg, return_dict={}):
        """Returns error dictionary in standard format.  If passed
           a return_dict, then adds to it, otherwise a new return_dict
           is created."""

        return_dict['error'] = msg
        return return_dict

    def httperror(self, res, body=None):
        """Returns a dict representing a non-OK HTTP response."""
        if body is None:
            body = res.read()
        return {
            'status-code': res.status,
            'reason-phrase': res.reason,
            'body': body
            }

    def remove_agent(self, aconn, reason="", send_alert=True):
        manager.remove_agent(aconn, reason=reason, send_alert=send_alert)
        if not manager.agent_conn_by_type(AgentManager.AGENT_TYPE_PRIMARY):
            # fixme: why get Session() from here?
            session = statusmon.Session()
            statusmon.remove_all_status(session)
            session.commit()
            session.close()

import logging

class StreamLogger(object):
    """
    File-like stream class that writes to a logger.
    Used for redirecting stdout & stderr to the log file.
    """

    def __init__(self, logger, tag=None):
        self.logger = logger
        self.tag = tag
        # writes are buffered to ensure full lines are printed together.
        self.buf = ''

    def writeln(self, line):
        line = line.rstrip()
        if not line:
            return
        if self.tag:
            line = '[' + self.tag + '] ' + line
        self.logger.log(logging.ERROR, line)

    def write(self, buf):
        buf = self.buf + buf
        self.buf = ''
        for line in buf.splitlines(True):
            if not line.endswith('\r') and not line.endswith('\n'):
                self.buf = self.buf + line
                continue
            self.writeln(line)

    def close(self):
        flush(self)

    def flush(self):
        self.writeln(self.buf)
        self.buf = ''

def main():
    import argparse
    import logger
    
    global server   # fixme
    global log      # fixme
    global manager   # fixme
    global statusmon # fixme
 
    parser = argparse.ArgumentParser(description='Palette Controller')
    parser.add_argument('config', nargs='?', default=None)
    parser.add_argument('--nostatus', action='store_true', default=False)
    args = parser.parse_args()

    config = Config(args.config)
    host = config.get('controller', 'host', default='localhost');
    port = config.getint('controller', 'port', default=9000);

    # loglevel is entirely controlled by the INI file.
    logger.make_loggers(config)
    log = logger.get(Controller.LOGGER_NAME)
    log.info("Controller version: %s", VERSION)

    # Log stderr to the log file too.
    # NOTE: stdout is not logged so that PDB will work.
    sys.stderr = StreamLogger(log, tag='STD')

    # database configuration
    url = config.get("database", "url")
    echo = config.getboolean("database", "echo", default=False)

    # engine is once per single application process.
    # see http://docs.sqlalchemy.org/en/rel_0_9/core/connections.html
    meta.engine = sqlalchemy.create_engine(url, echo=echo)
    # Create the table definition ONCE, before all the other threads start.
    meta.Base.metadata.create_all(bind=meta.engine)

    log.debug("Starting agent listener.")

    server = Controller((host, port), CliHandler)
    server.config = config
    server.log = log
    server.cli_get_status_interval = \
      config.get('controller', 'cli_get_status_interval', default=10)

    server.domainname = config.get('palette', 'domainname')
    server.domain = Domain()
    # FIXME: Pre-production hack: add domain if necessary
    server.domain.add(server.domainname)
    server.domainid = server.domain.id_by_name(server.domainname)

    global manager  # fixme: get rid of this global.
    manager = AgentManager(server)
    manager.update_last_disconnect_time()
    manager.start()

    # Need to instantiate to initialize state and status tables,
    # even if we don't run the status thread.
    statusmon = StatusMonitor(server, manager)
    server.statusmon = statusmon

    if not args.nostatus:
        log.debug("Starting status monitor.")
        statusmon.start()

    server.stateman = StateManager(server)

    server.serve_forever()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print "\nInterrupted.  Exiting."
        os._exit(1)
