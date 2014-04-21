#!/usr/bin/env python

import sys
import os
import shlex
import SocketServer as socketserver
import socket

import json
import time
import copy

from request import *
import exc

import httplib
import inspect
import ntpath

import sqlalchemy
from sqlalchemy.orm import sessionmaker, scoped_session
import meta

from agentmanager import AgentManager
from agentstatus import AgentStatusEntry
from backup import BackupManager
from state import StateManager, StateEntry
from status import StatusMonitor
from alert import Alert
from config import Config
from domain import Domain, DomainEntry
from profile import UserProfile

from version import VERSION

global manager # fixme
global server # fixme
global log # fixme

class CommandException(Exception):
    def __init__(self, errmsg):
        Exception.__init__(self, errmsg)

class Command(object):

    def __init__(self, line):
        self.dict = {}
        self.name = None
        self.args = []

        doing_dict = True
        for token in shlex.split(line):
            if doing_dict:
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
                else:
                    self.name = token
                    doing_dict = False
            else:
                self.args.append(token.strip())

        self.sanity()

    def sanity(self):
        opts = self.dict

        # FIXME: If we are passed no domain info but are passed a uuid,
        #        then get the domain from the agent table rather than
        #        exercise the 'only one domain in the database' hack.

        # A domainid is required. Validate passed domain information
        # against the database for existence and uniqueness.
        #
        # As an optimization, if only a domainid id is passed, with
        # no other domain information, accept it and use it.
        #
        # As a hack to aid development, if no domain information is
        # passed, and there is only one domain in the database, then
        # use it.
        #
        # FIXME: TBD: should this be farmed out to the Domain class?
        if 'domainid' in opts and not 'domainname' in opts:
            pass
        else:
            query = meta.Session.query(DomainEntry)
            if 'domainid' in opts:
                query = \
                  query.filter(DomainEntry.domainid == opts['domainid'])
            if 'domainname' in opts:
                query = \
                  query.filter(DomainEntry.domainname == opts['domainname'])
            try:
                entry = query.one()
                opts['domainid'] = entry.domainid
            except sqlalchemy.orm.exc.NoResultFound:
                 raise CommandException("no matching domain found")
            except sqlalchemy.orm.exc.MultipleResultsFound:
                 raise CommandException("domain must be unique")

        # Not all commands require an agent, but most do. For simplicity,
        # we require a uuid entry in the command dict, even if the
        # value of that entry is None. Validate passed agent
        # information, if any, against the database for existence
        # and uniqueness within the domain.
        #
        # As an optimization, if only a uuid is passed, with
        # no other agent information, accept it and use it.
        #
        # As a hack to aid development, if no agent information is
        # passed, and there is a (unique) primary in the database
        # for this domain, then use it.
        #
        # FIXME: TBD: should this be farmed out to the AgentStatusEntry class
        #             or AgentConnection class?
        if 'uuid' in opts and not 'displayname' in opts \
          and not 'hostname' in opts and not 'type' in opts:
            pass
        elif not 'uuid' in opts and not 'displayname' in opts \
          and not 'hostname' in opts and not 'type' in opts:
            query = meta.Session.query(AgentStatusEntry)
            query = query.filter(AgentStatusEntry.domainid == \
              opts['domainid'])
            query = query.filter(AgentStatusEntry.agent_type == \
                'primary')
            try:
                entry = query.one()
                opts['uuid'] = entry.uuid
            except sqlalchemy.orm.exc.NoResultFound:
                 opts['uuid'] = None
            except sqlalchemy.orm.exc.MultipleResultsFound:
                 opts['uuid'] = None
        else:
            query = meta.Session.query(AgentStatusEntry)
            query = query.filter(AgentStatusEntry.domainid == \
              opts['domainid'])
            if 'uuid' in opts:
                query = query.filter(AgentStatusEntry.uuid == \
                  opts['uuid'])
            if 'displayname' in opts:
                query = query.filter(AgentStatusEntry.displayname == \
                  opts['displayname'])
            if 'hostname' in opts:
                query = query.filter(AgentStatusEntry.hostname == \
                  opts['hostname'])
            if 'type' in opts:
                query = query.filter(AgentStatusEntry.agent_type == \
                  opts['type'])
            try:
                entry = query.one()
                opts['uuid'] = entry.uuid
            except sqlalchemy.orm.exc.NoResultFound:
                 raise CommandException("no matching agent found")
            except sqlalchemy.orm.exc.MultipleResultsFound:
                 raise CommandException("agent must be unique")

class CliHandler(socketserver.StreamRequestHandler):

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

    def ack(self):
        """ Acknowledge a submitted command before performing it. """
        print >> self.wfile, "OK"

    def error(self, msg, *args):
        if args:
            msg = msg % args
        self.print_client('[ERROR] ' + msg)

    def usage(self, msg):
        self.error('usage: '+msg)

    def print_client(self, fmt, *args):
        """
            Try to write fmt % args to self.wfile, which is
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

        line = fmt % args
        if not line.endswith('\n'):
            line += '\n'
        try:
            print  >> self.wfile, line
        except EnvironmentError:
            pass
#            line += '[TELNET] ' + line
#            sys.stdout.write(line)

    def do_help(self, cmd):
        print >> self.wfile, 'Optional prepended domain args:'
        print >> self.wfile, '    /domainid=id /domainname=name'
        print >> self.wfile, 'Optional prepended agent args:'
        print >> self.wfile, '    /displayname=name /hostname=name /uuid=uuid /type=type'
        for name, m in inspect.getmembers(self, predicate=inspect.ismethod):
            if name.startswith("do_"):
                name = name[3:].replace('_', '-')
                print >> self.wfile, '  ' + name
                if m.__doc__:
                    print >> self.wfile, '    ' + m.__doc__
                if hasattr(m, '__usage__'):
                    print >> self.wfile, '    usage: ' + m.__usage__
        print >> self.wfile

    def do_status(self, cmd):
        if len(cmd.args):
            self.error("'status' does not have an argument.")
            self.usage(self.do_status.__usage__)
            return

        aconn = self.get_aconn(cmd.dict)
        if not aconn:
            self.error('agent not found')
            return

        body = server.cli_cmd("tabadmin status -v", aconn)
        self.report_status(body)
    do_status.__usage__ = 'status'


    def do_backup(self, cmd):
        """ Perform a Tableau backup and potentially migrate. """

        target = None
        if len(cmd.args) > 1:
            self.usage(self.do_backup.__usage__)
            return
        elif len(cmd.args) == 1:
            target = cmd.args[0]

        aconn = self.get_aconn(cmd.dict)
        if not aconn:
            self.error('agent not found.')
            return

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
            return
        if states[StateEntry.STATE_TYPE_BACKUP] != StateEntry.STATE_BACKUP_NONE:
            print >> self.wfile, "FAIL: Can't backup - backup state is:", \
              states[StateEntry.STATE_TYPE_BACKUP]
            log.debug("Can't backup - backup state is: %s", \
              states[StateEntry.STATE_TYPE_BACKUP])
            return

        log.debug("-----------------Starting Backup-------------------")

        # fixme: lock to ensure against two simultaneous backups?
        stateman.update(StateEntry.STATE_TYPE_BACKUP, \
                            StateEntry.STATE_BACKUP_BACKUP)

        alert = Alert(self.server.config, log)
        alert.send("Backup Started")

        self.ack()

        body = server.backup_cmd(aconn, target)
        stateman.update(StateEntry.STATE_TYPE_BACKUP, \
          StateEntry.STATE_BACKUP_NONE)

        self.print_client(str(body))
        if not body.has_key('error'):
            alert.send("Backup Finished", body)
            return
        else:
            alert.send("Backup Failed", body)
            return
    do_backup.__usage__ = 'backup [target-displayname]'


    def do_restore(self, cmd):
        """Restore.  If the file/path we are restoring from is on a different
        machine than the Primary Agent, then get the file/path to the
        Primary Agent first."""

        if len(cmd.args) != 1:
            self.usage(self.do_restore.__usage__)
            return

        target = cmd.args[0]

        aconn = self.get_aconn(cmd.dict)
        if not aconn:
            self.error('agent not found')
            return

        # Check to see if we're in a state to restore
        stateman = self.server.stateman
        states = stateman.get_states()

        main_state = states[StateEntry.STATE_TYPE_MAIN]
        if main_state != StateEntry.STATE_MAIN_STARTED and \
                main_state != StateEntry.STATE_MAIN_STOPPED:
            self.error("can't backup - main state is: " + main_state)
            log.debug("can't restore - main state is: " + main_state)
            return

        backup_state = states[StateEntry.STATE_TYPE_BACKUP]
        if backup_state != StateEntry.STATE_BACKUP_NONE:
            self.error("can't restore - backup state is: " + backup_state)
            log.debug("can't restore - backup state is: " + backup_state)
            return

        # Do a backup before we try to do a restore.
        #FIXME: refactor do_backup() into do_backup() and backup()
        log.debug("------------Starting Backup for Restore--------------")

        # fixme: lock to ensure against two simultaneous backups?
        stateman.update(StateEntry.STATE_TYPE_BACKUP, \
                            StateEntry.STATE_BACKUP_BACKUP)

        alert = Alert(self.server.config, log)
        alert.send("Backup Started")

        self.ack()

        body = server.backup_cmd(aconn, target)
        stateman.update(StateEntry.STATE_TYPE_BACKUP, \
                            StateEntry.STATE_BACKUP_NONE)

        if not body.has_key('error'):
            alert.send("Backup Finished", body)
            backup_success = True
        else:
            alert.send("Backup Failed", body)
            backup_success = False

        if not backup_success:
            self.print_client("Backup failed.  Will still try to restore.")
            # fixme: Is this the right behavior?  In some cases
            # backup will fail, but restore will succeed.
            # The correct behavior is probably to have the UI
            # ask the user what they want to do.

        log.debug("-----------------Starting Restore-------------------")

        # fixme: lock to ensure against two simultaneous restores?
        stateman.update(StateEntry.STATE_TYPE_BACKUP, \
                            StateEntry.STATE_BACKUP_RESTORE1)

        body = server.restore_cmd(aconn, target)

        stateman.update(StateEntry.STATE_TYPE_BACKUP, StateEntry.STATE_BACKUP_NONE)
        # The "restore started" alert is done in restore_cmd(),
        # only after some sanity checking is done.
        alert = Alert(self.server.config, log)
        if not body.has_key('error'):
            alert.send("Restore Finished", body)
        else:
            alert.send("Restore Failed" , body)
        self.print_client(str(body))
    do_restore.__usage__ = 'restore [source:pathname]'

    def do_copy(self, cmd):
        """Copy a file from one agent to another."""

        if len(cmd.args) != 2:
            self.error(self.do_copy.__usage__)
            return

        body = server.copy_cmd(cmd.args[0], cmd.args[1])
        self.report_status(body)
    do_copy.__usage__ = 'copy source-agent-name:filename dest-agent-name'


    # FIXME: print status too
    def list_agents(self):
        agents = manager.all_agents()

        if len(agents) == 0:
            self.print_client('{}')
            return

        # FIXME: print the agent state too.
        s = ''
        for key in agents:
            d = copy.copy(agents[key].auth)
            d['displayname'] = agents[key].displayname
            s += str(d) + '\n'
        self.print_client(s)

    def list_backups(self):
        s = ''
        for backup in BackupManager.all():
            s += str(backup.todict()) + '\n'
        self.print_client(s)

    def do_list(self, cmd):
        """List information about all connected agents."""

        f = None
        if len(cmd.args) == 0:
            f = self.list_agents
        elif len(cmd.args) == 1:
            if cmd.args[0].lower() == 'agents':
                f = self.list_agents
            elif cmd.args[0].lower() == 'backups':
                f = self.list_backups
        if f is None:
            self.usage(self.do_list.__usage__)
            return

        self.ack()
        f()
    do_list.__usage__ = 'list [agents|backups]'

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
        if len(cmd.args) < 2:
            self.error(self.do_pget.__usage__)
            return

        aconn = self.get_aconn(cmd.dict)
        if not aconn:
            self.error('agent not found')
            return

        pget_cmd = Controller.PGET_BIN
        for arg in cmd.args:
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
    do_pget.__usage__ = 'pget https://...... local-name'


    def do_firewall(self, cmd):
        if len(cmd.args) == 1 or len(cmd.args) > 2:
            self.error(self.do_firewall.__usage__)
            return

        aconn = self.get_aconn(cmd.dict)
        if not aconn:
            self.error('agent not found')
            return

        if len(cmd.args) == 0:
            self.ack()
            body = server.firewall(aconn, "GET")
            print >> self.wfile, body
            return

        try:
            fw_port = int(cmd.args[0])
        except ValueError, e:
            self.error("firewall: Invalid port: " + cmd.args[0])
            return

        if cmd.args[1] == 'enable':
            action = 'enable'
        elif cmd.args[1] == 'disable':
            action = 'disable'
        else:
            self.error(self.do_firewall.__usage__)
            return

        self.ack()

        send_body_dict = {
            "num": fw_port,
            "action": action
        }

        body = server.firewall(aconn, "POST", send_body_dict)
        print >> self.wfile, body
        return

    do_firewall.__usage__ = 'firewall port# { enable | disable }\n   or\n           firewall'


    def do_ping(self, cmd):
        """Ping an agent"""
        if len(cmd.args):
            self.error(self.do_ping.__usage__)
            return

        aconn = self.get_aconn(cmd.dict)
        if not aconn:
            self.error('agent not found')
            return

        print >> self.wfile, "Sending ping to displayname '%s' (type: %s)." % \
          (aconn.displayname, aconn.auth['type'])

        body = server.ping(aconn)
        self.report_status(body)

    do_ping.__usage__ = 'ping'

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
        self.ack()

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
            stateman.update(StateEntry.STATE_TYPE_MAIN,
                            StateEntry.STATE_MAIN_STOPPED)

        # STARTED is set by the status monitor since it really knows the status.
        self.print_client(str(body))

    def do_stop(self, cmd):
        if len(cmd.args) != 0:
            self.error(self.do_stop.__usage__)
            return

        aconn = self.get_aconn(cmd.dict)
        if not aconn:
            self.error('agent not found')
            return

        # Check to see if we're in a state to stop
        stateman = self.server.stateman
        states = stateman.get_states()
        if states[StateEntry.STATE_TYPE_MAIN] != StateEntry.STATE_MAIN_STARTED:
            self.error("can't stop - main state is: " +\
                           states[StateEntry.STATE_TYPE_MAIN])
            self.error("can't stop - current state is: " +\
                           states[StateEntry.STATE_TYPE_MAIN])
            return

        log.debug("------------Starting Backup for Stop---------------")
        # fixme: lock to ensure against two simultaneous backups?
        stateman.update(StateEntry.STATE_TYPE_BACKUP, \
          StateEntry.STATE_BACKUP_BACKUP)

        alert = Alert(self.server.config, log)
        alert.send("Backup Started")

        self.ack()

        body = server.backup_cmd(aconn)
        stateman.update(StateEntry.STATE_TYPE_BACKUP, \
                            StateEntry.STATE_BACKUP_NONE)

        if not body.has_key('error'):
            alert.send("Backup Finished", body)
        else:
            alert.send("Backup Failed", body)
            # FIXME: return JSON
            self.print_client("Backup failed.  Will not attempt stop.")
            return

        # Note: Make sure to set the state in the database before
        # we report "OK" back to the client since "OK" to the UI client
        # results in an immediate check of the state.
        stateman.update(StateEntry.STATE_TYPE_MAIN,
                        StateEntry.STATE_MAIN_STOPPING)

        log.debug("-----------------Stopping Tableau-------------------")
        # fixme: Prevent stopping if the user is doing a backup or restore?
        # fixme: Reply with "OK" only after the agent received the command?

        body = server.cli_cmd('tabadmin stop', aconn)
        if not body.has_key("error"):
            # Start the maintenance server only after Tableau has stopped
            # and reqlinquished the web server port.
            maint_body = server.maint("start")
            if maint_body.has_key("error"):
                self.print_client("maint start failed: " + str(maint_body))

        # STOPPED is set by the status monitor since it really knows the status.

        # fixme: check & report status to see if it really stopped?
        self.print_client(str(body))
    do_stop.__usage__ = 'stop'

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
        """Start or Stop the maintenance webserver on the agent."""

        if len(cmd.args) < 1 or len(cmd.args) > 2:
            self.usage(self.do_maint.__usage__)
            return

        action = cmd.args[0].lower()
        if action != "start" and action != "stop":
            self.usage(self.do_maint.__usage__)
            return

        port = -1
        if len(cmd.args) == 2:
            try:
                port = int(cmd.args[1])
            except ValueError, e:
                self.error("invalid port '%s', number required.", cmd.args[1])
                return;

        self.ack()

        body = server.maint(action, port)
        self.print_client(str(body))
    do_maint.__usage__ = 'maint [start|stop]'

    def do_archive(self, cmd):
        """Start or Stop the archive HTTPS server on the agent."""
        if len(cmd.args) < 1 or len(cmd.args) > 2:
            self.usage(self.do_archive.__usage__)
            return

        aconn = self.get_aconn(cmd.dict)
        if not aconn:
            self.error('agent not found')
            return

        action = cmd.args[0].lower()
        if action != "start" and action != "stop":
            self.usage(self.do_archive.__usage__)
            return

        port = -1
        if len(cmd.args) == 2:
            try:
                port = int(cmd.args[1])
            except ValueError, e:
                self.error("invalid port '%s', number required.", cmd.args[1])
                return;

        self.ack()

        body = server.archive(aconn, action, port)
        self.print_client(str(body))
    do_archive.__usage__ = 'archive [start|stop] [port]'

    do_maint.__usage__ = 'maint [start|stop]'

    def do_displayname(self, cmd):
        """Set the display name for an agent"""
        if len(cmd.args) != 1:
            self.error(self.do_displayname.__usage__)
            return

        new_displayname = cmd.args[0]
        uuid = cmd.dict['uuid']

        # Note: aconn will be None if agent is not connected, which is OK
        aconn = manager.agent_conn_by_uuid(uuid)

        try:
            server.displayname_cmd(aconn, uuid, new_displayname)
            self.ack()
        except ValueError, e:
            self.error(str(e))

    do_displayname.__usage__ = 'displayname new-displayname'

    def do_nop(self, cmd):
        """usage: nop"""

        print >> self.wfile, "dict:"
        for key in cmd.dict:
            print >> self.wfile, "\t%s = %s" % (key, cmd.dict[key])

        print >> self.wfile, "command:"
        print >> self.wfile, "\t%s" % (cmd.name)

        print >> self.wfile, "args:"
        for arg in cmd.args:
            print >> self.wfile, "\t%s" % (arg)

        self.ack()

    def get_aconn(self, opts):
        # FIXME: This method is a temporary hack while we
        #        clean up the telnet commands
        # FIXME: TBD: Should this be farmed out to another class?

        aconn = None

        if opts.has_key('uuid'): # should never fail
            uuid = opts['uuid'] # may be None
            if uuid:
                aconn = manager.agent_conn_by_uuid(uuid)
                if not aconn:
                    self.error("No connected agent with uuid=%s", uuid)
            else:
                self.error("No agent specified")
        else: # should never happen
            self.error("No agent specified")

        return aconn

    def handle(self):
        while True:
            data = self.rfile.readline().strip()
            if not data: break

            try:
                cmd = Command(data)
            except CommandException, e:
                self.error(str(e))
                continue

            if not hasattr(self, 'do_'+cmd.name):
                self.error('invalid command: %s', cmd.name)
                continue

            # <command> /displayname=X /type=primary, /uuid=Y, /hostname=Z [args]
            f = getattr(self, 'do_'+cmd.name)
            f(cmd)


class Controller(socketserver.ThreadingMixIn, socketserver.TCPServer):

    LOGGER_NAME = "main"
    allow_reuse_address = True

    PGET_BIN = "pget.exe"

    def backup_cmd(self, aconn, target=None):
        """Perform a backup - not including any necessary migration."""
        # fixme: make sure another backup isn't already running?

        # Note: In a backup context 'target' is the destination for the backup,
        #       while in a restore context, 'target' is the source.

        # Example name: Jan27_162225.tsbak
        backup_name = time.strftime("%b%d_%H%M%S") + ".tsbak"

        # aconn is the primary
        install_dir = aconn.auth['install-dir']
        backup_path = ntpath.join(install_dir, "Data", backup_name)

        # e.g.: c:\\Program\ Files\ (x86)\\Palette\\Data\\Jan27_162225.tsbak
        cmd = 'tabadmin backup \\\"%s\\\"' % backup_path
        body = self.cli_cmd(cmd, aconn)
        if body.has_key('error'):
            return body

        agents = manager.all_agents()

        # target_conn is the destination agent - if applicable.
        target_conn = None
        if target != None:
            for key in agents:
                if agents[key].displayname == target:
                    # FIXME: make sure agent is connected
                    if agents[key].auth['type'] != \
                      AgentManager.AGENT_TYPE_PRIMARY:
                        target_conn = agents[key]
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
                    if target_conn == None:
                        target_conn = agents[key]
                    else:
                        if agents[key].displayname < \
                          target_conn.displayname:
                            target_conn = agents[key]
        if target:
            self.error("agent %s does not exist or is offline" % target)

        if target_conn:
            backup_loc = target_conn
            # Copy the backup to a non-primary agent
            source_path = "%s:%s" % (aconn.displayname, backup_name)
            copy_body = self.copy_cmd(source_path, target_conn.displayname)

            if copy_body.has_key('error'):
                msg = ("Copy of backup file '%s' to agent '%s' failed. "+\
                    "Will leave the backup file on the primary agent. "+\
                    "Error was: %s") \
                    % (backup_name, target_conn.displayname, copy_body['error'])
                self.log.info(msg)
                body['info'] = msg
                # Something was wrong with the copy to the non-primary agent.
                #  Leave the backup on the primary after all.
                backup_loc = aconn
            else:
                # The copy succeeded.
                # Remove the backup file from the primary
                remove_cli = 'CMD /C DEL \\\"%s\\\"' % backup_path
                remove_body = self.cli_cmd(remove_cli, aconn)

                # Check if the DEL worked.
                if remove_body.has_key('error'):
                    body['info'] = ("DEL of backup file failed after copy. "+\
                        "Command: '%s'. Error was: %s") \
                        % (remove_cli, remove_body['error'])
        else:
            backup_loc = aconn
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

        body = self._send_cli(command, aconn)

        if body.has_key('error'):
            return body

        if not body.has_key('run-status'):
            return self.error("_send_cli (%s) body response missing 'run-status: '" % \
                (command, str(e)))

        # It is possible for the command to finish immediately.
        if body['run-status'] == 'finished':
            return body

        cli_body = self._get_status("cli", body['xid'], aconn, command)

        if not cli_body.has_key("stdout"):
            self.log.error("check status of cli failed - missing 'stdout' in reply", cli_body)
            return self.error(\
                "Missing 'stdout' in agent reply for command '%s'" % command,
                                                                    cli_body)

        cleanup_body = self._send_cleanup("cli", body['xid'], aconn, command)

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

        self.log.debug("about to send the cli command to '%s', type '%s' xid: %d, command: %s",
                aconn.displayname, aconn.auth['type'], req.xid, cli_command)
        try:
            aconn.httpconn.request('POST', '/cli', req.send_body, headers)
            self.log.debug('sent cli command.')

            res = aconn.httpconn.getresponse()

            self.log.debug('_send_cli: command: cli: ' + str(res.status) + ' ' + str(res.reason))
            # print "headers:", res.getheaders()
            self.log.debug("_send_cli reading...")
            body_json = res.read()

            if res.status != httplib.OK:
                self.log.error("_send_cli: command: '%s', res.status != 200: %d, reason: %s, body: %s",
                        cli_command, res.status, res.reason, body_json)
                raise exc.HTTPException("res.status != 200: %d, reason: %s" % \
                                        (res.status, res.reason), body_json)
        except exc.HTTPException as e:
            self.log.error(\
                "_send_cli: command '%s' failed with exc.HTTPException: %s",
                                                        cli_command, str(e))
            # bad agent
            self.remove_agent(aconn, "Command sent to agent failed. Error: " + str(e))
            return self.error("_send_cli: '%s' command failed.  Error: %s, body: %s" %
                                (cli_command, str(e), e.body), e.body)
        except (httplib.HTTPException, EnvironmentError) as e:
            self.log.error(\
                "_send_cli: command '%s' failed with httplib.HTTPException: %s",
                                                        cli_command, str(e))

            self.remove_agent(aconn, "Communication lost with agent.") # bad agent
            return self.error("_send_cli: '%s' command failed with: %s" %
                            (cli_command, str(e)))
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

    def _send_cleanup(self, command, xid, aconn, orig_cli_command):
        """Send a "cleanup" command to an Agent.
            On success, returns the body of the reply.
            On failure, throws an exception.

            orig_cli_command is used only for debugging/printing.

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
            body_json = res.read()
            if res.status != httplib.OK:
                self.log.error("_send_cleanup: POST %s for original command '%s' failed with res.status != 200: %d, reason: %s, body: %s",
                     command, orig_cli_command, res.status, res.reason, body_json)
                raise exc.HTTPException("res.status != 200: %d, reason: %s" % \
                                        (res.status, res.reason), body_json)

            self.log.debug("headers: " + str(res.getheaders()))
            self.log.debug("_send_cleanup reading...")
        except exc.HTTPException, e:
            self.log.error(\
                "_send_cleanup: exc.HTTPExcpetion %s for original command '%s' failed with: %s, body: %s",
                            command, orig_cli_command, str(e), e.body)
            # bad agent
            self.remove_agent(aconn, "Command to agent failed with error: " + str(e))
            return self.error("_send_cleanup '%s' for original command '%s' failed.  Error: %s, body: %s" % \
                    (command, orig_cli_command, str(e), e.body))
        except (httplib.HTTPException, EnvironmentError) as e:
            # bad agent
            self.log.error("_send_cleanup: POST /%s for original command '%s' failed with: %s",
                                            command, orig_cli_command, str(e))
            self.remove_agent(aconn, "Command to agent failed. Error: " + str(e))
            return self.error("'%s' failed for original command '%s' with: %s" %
                                    (command, orig_cli_command, str(e)))
        finally:
            # Must call aconn.unlock() even after self.remove_agent(),
            # since another thread may waiting on the lock.
            aconn.unlock()
            self.log.debug("_send_cleanup unlocked")

        self.log.debug("done reading.")
        body = json.loads(body_json)
        if body == None:
            return self.error("POST /%s getresponse returned a null body" % command)
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
                self.log.info("copy_cmd: agent with conn_id '%d' is now gone and won't be checked.", key)
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

        target_dir = ntpath.join(dst.auth['install-dir'], 'Data')

        command = '%s https://%s:%s/%s "%s"' % \
            (Controller.PGET_BIN, source_ip, src.auth['listen-port'],
             source_path, target_dir)

        # Send command to destination agent
        copy_body = self.cli_cmd(command, dst)
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
        # Without a ':', assume the backup is still on the primary.
        parts = target.split(':')
        if len(parts) == 1:
            source_displayname = aconn.displayname
            source_filename = parts[0]
        elif len(parts) == 2:
            source_displayname = parts[0]
            source_filename = parts[1]
        else:
            return self.error('Invalid target: ' + target)

        if os.path.isabs(source_filename):
            return self.error("[ERROR] May not specify an absolute pathname or disk: " + source_filename)

        install_dir = aconn.auth['install-dir']
        source_fullpathname = ntpath.join(install_dir, "Data", source_filename)

        # Check if the source_filename is on the Primary Agent.
        if source_displayname != aconn.displayname:
            # The source_filename isn't on the Primary agent:
            # We need to copy the file to the Primary.

            # copy_cmd arguments:
            #   source-agent-name:/filename
            #   dest-agent-displayname
            self.log.debug("restore: Sending copy command: %s, %s", \
                               target, aconn.displayname)
            body = server.copy_cmd(target, aconn.displayname)

            if body.has_key("error"):
                fmt = "restore: copy backup file '%s' from '%s' failed. " +\
                    "Error was: %s"
                self.log.debug(fmt,
                               source_fullpathname,
                               source_displayname,
                               body['error'])
                return body

        # The restore file is now on the Primary Agent.

        alert = Alert(self.config, log)
        alert.send("Restore Started")

        stateman = server.stateman
        orig_states = stateman.get_states()
        main_state = orig_states[StateEntry.STATE_TYPE_MAIN]
        if main_state == StateEntry.STATE_MAIN_STARTED:
            # Restore can run only when tableau is stopped.
            stateman.update(StateEntry.STATE_TYPE_MAIN, \
                                StateEntry.STATE_MAIN_STOPPING)
            log.debug("------------Stopping Tableau for restore-------------")
            stop_body = self.cli_cmd("tabadmin stop", aconn)
            if stop_body.has_key('error'):
                self.log.info("Restore: tabadmin stop failed")
                if source_displayname != aconn.displayname:
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
                if source_displayname != aconn.displayname:
                    # If the file was copied to the Primary, delete
                    # the temporary backup file we copied to the Primary.
                    self.delete_file(aconn, source_fullpathname)
                return self.error('Tableau did not stop as requested.  ' +
                                  'Restore aborted.')

        # 'tabadmin restore ...' starts tableau as part of the restore procedure.
        # fixme: Maybe the maintenance web server wasn't running?
        maint_msg = ""
        maint_body = server.maint("stop")
        if maint_body.has_key("error"):
            self.log.info("Restore: maint stop failed: " + maint_body['error'])
            # continue on, not a fatal error...
            maint_msg = "Restore: maint stop failed.  Error was: %s" \
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

        if maint_msg != "":
            restore_body['info'] = maint_msg

        # fixme: Do we need to add restore information to the database?
        # fixme: check status before cleanup? Or cleanup anyway?

        if source_displayname != aconn.displayname:
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
        self.log.debug("Removing file '%s'", source_fullpathname)
        cmd = 'CMD /C DEL \\\"%s\\\"' % source_fullpathname
        remove_body = self.cli_cmd(cmd, aconn)
        if remove_body.has_key('error'):
            self.log.info('DEL of "%s" failed.', source_fullpathname)
            # fixme: report somewhere the DEL failed.
        return remove_body

    def _get_status(self, command, xid, aconn, orig_cli_command):
        """Gets status on the command and xid.  Returns:
            Body in json with status/results.

            orig_cli_command is used only for debugging/printing.

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
            self.log.debug("about to get status of command %s, '%s', xid %d",
                    command, orig_cli_command, xid)

            if not manager.agent_connected(aconn):
                self.log.info("Agent '%s' (type: '%s', conn_id %d) disconnected before finishing: %s",
                    aconn.displayname, aconn.auth['type'], aconn.conn_id, uri)
                return self.error("Agent '%s' (type: '%s', conn_id %d) disconnected before finishing: %s" %
                    (aconn.displayname, aconn.auth['type'], aconn.conn_id, uri))

            aconn.lock()
            self.log.debug("Sending GET " + uri)

            try:
                aconn.httpconn.request("GET", uri, None, headers)

                self.log.debug("Getting response from GET " +  uri)
                res = aconn.httpconn.getresponse()
                self.log.debug("status: " + str(res.status) + ' ' + str(res.reason))
                if res.status != httplib.OK:
                    self.remove_agent(aconn, "Failed status from agent.")
                    return self.error("GET %s command failed with: %s" % (uri, str(e)))
#                debug for testing agent disconnects
#                print "sleeping"
#                time.sleep(5)
#                print "awake"

                self.log.debug("_get_status reading.")
                body_json = res.read()
                aconn.unlock()

                body = json.loads(body_json)
                if body == None:
                    return self.error("Get /%s getresponse returned a null body" % uri)

                self.log.debug("body = " + str(body))
                if not body.has_key('run-status'):
                    self.remove_agent(aconn, "Agent returned invalid status.")
                    return self.error("GET %s command reply was missing 'run-status'!  Will not retry." % (uri), body)

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

    def firewall(self, aconn, method, send_body_dict={}):
        """Sends a firewall GET or POST command.
           Returns the body result.
        """

        if method == "GET":
            send_body = ""
        else:
            send_body = json.dumps(send_body_dict)

        return self.send_immediate(aconn, method, "/firewall", send_body)

    def maint(self, action, port=-1):
        # Get the Primary Agent handle
        # FIXME: Tie agent to domain; better, pass aconn to this method.
        aconn = manager.agent_conn_by_type(AgentManager.AGENT_TYPE_PRIMARY)

        if not aconn:
            return self.error("maint: no primary agent is connected.")

        send_body = {"action": action}
        if port > 0:
            send_body["port"] = port

        return self.send_immediate(aconn, "POST", "/maint", send_body)

    def archive(self, aconn, action, port=-1):
        send_body = {"action": action}
        if port > 0:
            send_body["port"] = port

        return self.send_immediate(aconn, "POST", "/archive", send_body)

    def ping(self, aconn):

        return self.send_immediate(aconn, "POST", "/ping")


    def send_immediate(self, aconn, method, uri, send_body=""):
        """Sends the request specified by:
                aconn:      agent connection to send to.
                method:     POST, PUT, GET, etc.
                uri:        '/maint', 'firewall', etc.
                send_body:  Body to send in the request.
                            Can be a dictionary or a string.
                            If it is a dictionary, it will be converted
                            to a string (json).
            Returns the body result.
        """

        if type(send_body) == dict:
            send_body = json.dumps(send_body)

        headers = {"Content-Type": "application/json"}

        self.log.debug("about to send an immediate command to '%s', type '%s', method '%s', uri '%s', body '%s'",
                aconn.displayname, aconn.auth['type'], method, uri, send_body)

        aconn.lock()
        body = {}
        try:
            aconn.httpconn.request(method, uri, send_body, headers)
            res = aconn.httpconn.getresponse()

            rawbody = res.read()
            if res.status != httplib.OK:
                # bad agent
                self.remove_agent(aconn, "Communication failure with agent.  Immediate command to %s, status returned: %d: %s %s, body: %s" % \
                        (aconn.displayname, res.status, method, uri, rawbody))
                self.log.error("immediate command to %s failed with status %d: %s %s, body:",
                            aconn.displayname, res.status, method, rawbody)
                return self.httperror(res, agent=aconn.displayname,
                                      method=method, uri=uri, body=rawbody);
            elif rawbody:
                body = json.loads(rawbody)
                self.log.debug("send_immediate for %s %s reply: %s",
                                                    method, uri, str(body))
            else:
                body = {}
                self.log.debug("send_immediate for %s %s reply empty.",
                                                                method, uri)
        except (httplib.HTTPException, EnvironmentError) as e:
            self.log.error("Agent send_immediate command %s %s failed: %s",
                                        method, uri, str(e))    # bad agent
            self.remove_agent(aconn, \
                    "Agent send_immediate command %s %s failed: %s" % \
                                        (method, uri, str(e)))    # bad agent
            return self.error("send_immediate for method %s, uri %s failed: %s" % \
                                                    (method, uri, str(e)))
        finally:
            aconn.unlock()

        self.log.debug("send immediate %s %s success, response: %s", \
                                                method, uri, str(body))
        return body

    def displayname_cmd(self, aconn, uuid, displayname):
        """Sets displayname for the agent with the given hostname. At
           this point assumes hostname is unique in the database."""

        manager.set_displayname(aconn, uuid, displayname)

    def error(self, msg, return_dict={}):
        """Returns error dictionary in standard format.  If passed
           a return_dict, then adds to it, otherwise a new return_dict
           is created."""

        return_dict['error'] = msg
        return return_dict

    def httperror(self, res, error='HTTP failure',
                  agent=None, method=None, uri=None, body=None):
        """Returns a dict representing a non-OK HTTP response."""
        if body is None:
            body = res.read()
        d = {
            'error': error,
            'status-code': res.status,
            'reason-phrase': res.reason,
            }
        if method:
            d['method'] = method
        if uri:
            d['uri'] = uri
        if body:
            d['body'] = body
        return d;

    def remove_agent(self, aconn, reason="", send_alert=True):
        manager.remove_agent(aconn, reason=reason, send_alert=send_alert)
        # FIXME: At the least, we need to add the domain to the check
        #        for a primary; better, however, would be to store the
        #        uuid of the status with the status and riff off uuid.
        if not manager.agent_conn_by_type(AgentManager.AGENT_TYPE_PRIMARY):
            session = meta.Session()
            statusmon.remove_all_status()
            session.commit()

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
    meta.Session = scoped_session(sessionmaker(bind=meta.engine))

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
