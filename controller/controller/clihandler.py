import copy
import inspect
import os
import sys
import shlex
import SocketServer as socketserver
import socket
import json
import traceback

import sqlalchemy

from akiri.framework.ext.sqlalchemy import meta
import exc

from agent import Agent
from agentmanager import AgentManager
from backup import BackupManager
from event_control import EventControl
from gcs import GCS
from s3 import S3
from system import SystemEntry
from state import StateManager
from tableau import TableauStatusMonitor, TableauProcess

from cli_errors import *

def usage(msg):
    def wrapper(f):
        def realf(*args, **kwargs):
            return f(*args, **kwargs)
        realf.__name__ = f.__name__
        realf.__usage__ = msg
        return realf
    return wrapper

class CommandException(Exception):
    def __init__(self, errmsg):
        Exception.__init__(self, errmsg)

class Command(object):

    def __init__(self, server, line):
        # FIXME: temporary hack to get domainid and envid
        self.server = server
        self.dict = {}
        self.name = None
        self.args = []

        try: 
            tokens = shlex.split(line)
        except ValueError, e:
             raise CommandException(str(e))

        doing_dict = True
        for token in tokens:
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

        # This fills in any missing information in the opts dict.
        self.sanity()

    def sanity(self):
        opts = self.dict

        # FIXME: domain/env HACK
        if not 'domainid' in opts:
            opts['domainid'] = self.server.domain.domainid
        if not 'envid' in opts:
            opts['envid'] = self.server.environment.envid

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
        if 'uuid' in opts and not 'displayname' in opts \
          and not 'hostname' in opts and not 'type' in opts:
            pass
        elif not 'uuid' in opts and not 'displayname' in opts \
          and not 'hostname' in opts and not 'type' in opts:
            query = meta.Session.query(Agent)
            query = query.filter(Agent.envid == opts['envid'])
            query = query.filter(Agent.agent_type == 'primary')
            try:
                entry = query.one()
                opts['uuid'] = entry.uuid
            except sqlalchemy.orm.exc.NoResultFound:
                 opts['uuid'] = None
            except sqlalchemy.orm.exc.MultipleResultsFound:
                 opts['uuid'] = None
        else:
            query = meta.Session.query(Agent)
            query = query.filter(Agent.envid == opts['envid'])
            if 'uuid' in opts:
                query = query.filter(Agent.uuid == opts['uuid'])
            if 'displayname' in opts:
                query = query.filter(\
                    Agent.displayname == opts['displayname'])
            if 'hostname' in opts:
                query = query.filter(Agent.hostname == opts['hostname'])
            if 'type' in opts:
                query = query.filter(Agent.agent_type == opts['type'])
            try:
                entry = query.one()
                opts['uuid'] = entry.uuid
            except sqlalchemy.orm.exc.NoResultFound:
                 raise CommandException("no matching agent found")
            except sqlalchemy.orm.exc.MultipleResultsFound:
                 raise CommandException("agent must be unique")

        if 'userid' in opts:
            if not opts['userid'].isdigit():
                 raise CommandException("Invalid userid: must be an integer.")

class CliHandler(socketserver.StreamRequestHandler):

    # Valid choices for JSON "status"
    STATUS_OK="OK"
    STATUS_ERROR="error"

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
        self.print_client("OK")

    def error(self, errnum, *args):
        if args:
            if len(args) == 1:
                msg = args[0]
            else:
                msg = args[0] % args[1:]
        else:
            if errnum in error_strings:
                msg = error_strings[errnum]
            else:
                msg = "No additional information"

        text = "ERROR %d %s" % (errnum, msg)
        self.print_client(text)

    def success(self, body):
        if 'error' in body:
            return False
        else:
            return True

    def failed(self, body):
        if 'error' in body:
            return True
        else:
            return False

    def print_usage(self, msg):
        self.error(ERROR_USAGE, 'usage: '+msg)

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

        try:
            line = fmt % args
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            line = "ERROR %d %s.  fmt: '%s', args: '%s', Traceback: %s" % \
                (ERROR_INTERNAL,
                    sys.exc_info()[1],
                        str(fmt), str(args),
                        ''.join(traceback.format_tb(exc_traceback)).\
                                                        replace('\n', ''))
#        if not line.endswith('\n'):
#            line += '\n'
        try:
            print  >> self.wfile, line
        except EnvironmentError:
            pass
#            line += '[TELNET] ' + line
#            sys.stdout.write(line)

    def report_status(self, body):
        if self.success(body):
            body['status'] = CliHandler.STATUS_OK
        else:
            body['status'] = CliHandler.STATUS_ERROR

        self.print_client("%s", json.dumps(body))

    def do_help(self, cmd):
        self.print_client('Optional prepended domain args:')
        self.print_client('    /domainid=id /domainname=name')
        self.print_client('Optional prepended agent args:')
        self.print_client('    /displayname=name /hostname=name ' + \
                                                    '/uuid=uuid /type=type')
        for name, m in inspect.getmembers(self, predicate=inspect.ismethod):
            if name.startswith("do_"):
                name = name[3:].replace('_', '-')
                self.print_client('  ' + name)
                if m.__doc__:
                    self.print_client('    ' + m.__doc__)
                if hasattr(m, '__usage__'):
                    self.print_client('    usage: ' + m.__usage__)
        self.print_client("\n")

    @usage('status')
    def do_status(self, cmd):
        if len(cmd.args):
            self.error(ERROR_USAGE, "'status' does not have an argument.")
            self.print_usage(self.do_status.__usage__)
            return

        agent = self.get_agent(cmd.dict)
        if not agent:
            # The error has already been displayed in get_agent()
            return

        self.ack()
        body = self.server.cli_cmd("tabadmin status -v", agent)
        self.report_status(body)

    @usage('upgrade [on | off]')
    def do_upgrade(self, cmd):
        stateman = self.server.stateman

        if not len(cmd.args):
            main_state = stateman.get_state()
            self.ack()
            self.report_status({"main-state": main_state})
            return
        if len(cmd.args) != 1:
            self.print_usage(self.do_upgrade.__usage__)
            return
        if cmd.args[0] not in ('on', 'off'):
            self.print_usage(self.do_upgrade.__usage__)
            return

        agent = self.get_agent(cmd.dict, error_on_no_agent=False)

        # Note: an agent doesn't have to be connected to change upgrade mode.

        if agent:
            aconn = agent.connection
        else:
            aconn = None

        # lock to ensure against two simultaneous user actions
        if aconn and not aconn.user_action_lock(blocking=False):
            self.error(ERROR_BUSY)
            return

        # Check to see if we're in a state to upgrade
        main_state = stateman.get_state()

        if cmd.args[0] == 'on':
            if main_state not in (StateManager.STATE_STARTED,
                    StateManager.STATE_STOPPED, StateManager.STATE_DEGRADED,
                    StateManager.STATE_DISCONNECTED,
                                                    StateManager.STATE_UNKNOWN):

                self.error(\
                        ERROR_BUSY, "FAIL: Can't upgrade - main state is: %s",
                                                                  main_state)
                self.server.log.debug("Can't upgrade - main state is: %s",
                                                                    main_state)
                if aconn:
                    aconn.user_action_unlock()
                return

            stateman.update(StateManager.STATE_UPGRADING)
            if aconn:
                aconn.user_action_unlock()

            self.ack()
            self.report_status({})
            return

        # "upgrade off"
        if main_state != StateManager.STATE_UPGRADING:
            self.error(ERROR_BUSY, "FAIL: Can't upgrade - main state is: %s",
                                                              main_state)
            self.server.log.debug("Can't upgrade - main state is: %s",
                                                                    main_state)

            if aconn:
                aconn.user_action_unlock()
            return

        # Set it back to the real state
        self.server.statusmon.set_main_state_from_tableau_status()

        if aconn:
            aconn.user_action_unlock()

        self.ack()
        self.report_status({})

    @usage('backup')
    def do_backup(self, cmd):
        """Perform a Tableau backup and potentially migrate."""

        if len(cmd.args):
            self.print_usage(self.do_backup.__usage__)
            return

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        aconn = agent.connection

        # lock to ensure against two simultaneous user actions
        if not aconn.user_action_lock(blocking=False):
            self.error(ERROR_BUSY)
            return

        # Check to see if we're in a state to backup
        stateman = self.server.stateman
        main_state = stateman.get_state()

        # Backups can be done when Tableau is started, degraded or stopped.
        if main_state not in (StateManager.STATE_STARTED,
                    StateManager.STATE_DEGRADED, StateManager.STATE_STOPPED):
            self.error(ERROR_BUSY, "FAIL: Can't backup - main state is: %s",
                                                                  main_state)
            self.server.log.debug("Can't backup - main state is: %s",
                                                                    main_state)
            aconn.user_action_unlock()
            return

        reported_status = self.server.statusmon.get_reported_status()
        # The reported status from tableau needs to be running or stopped
        # to do a backup.
        if reported_status in (TableauProcess.STATUS_RUNNING,
                                        TableauProcess.STATUS_DEGRADED):
            stateman.update(StateManager.STATE_STARTED_BACKUP)
        elif reported_status == TableauProcess.STATUS_STOPPED:
            stateman.update(StateManager.STATE_STOPPED_BACKUP)
        else:
            self.error(ERROR_WRONG_STATE, 
                        "FAIL: Can't backup - reported status is: %s",
                                                              reported_status)
            self.server.log.debug("Can't backup - reported status is: %s", \
                                                            reported_status)
            aconn.user_action_unlock()
            return

        self.server.log.debug("-----------------Starting Backup-------------------")
        if cmd.dict.has_key('userid'):
            userid = int(cmd.dict['userid'])
        else:
            userid = None

        if userid != None:
            backup_started_event = EventControl.BACKUP_STARTED
            backup_finished_event = EventControl.BACKUP_FINISHED
            backup_failed_event = EventControl.BACKUP_FAILED
        else:
            backup_started_event = EventControl.BACKUP_STARTED_SCHEDULED
            backup_finished_event = EventControl.BACKUP_FINISHED_SCHEDULED
            backup_failed_event = EventControl.BACKUP_FAILED_SCHEDULED

        self.server.event_control.gen(backup_started_event,
                                      agent.__dict__, userid=userid)

        self.ack()

        body = self.server.backup_cmd(agent)

        if self.success(body):
            self.server.event_control.gen(backup_finished_event,
                        dict(body.items() + agent.__dict__.items()),
                        userid=userid)
        else:
            self.server.event_control.gen(backup_failed_event,
                        dict(body.items() + agent.__dict__.items()),
                        userid=userid)

        if reported_status == TableauProcess.STATUS_RUNNING:
            stateman.update(StateManager.STATE_STARTED)
        elif reported_status == TableauProcess.STATUS_STOPPED:
            stateman.update(StateManager.STATE_STOPPED)

        # Get the latest status from tabadmin
        self.server.statusmon.check_status_with_connection(agent)
        # Don't unlock to allow the status thread to ALSO do
        # 'tabadmin status -v' until at least we finish with ours.
        aconn.user_action_unlock()

        self.report_status(body)


    @usage('backupdel backup-name')
    def do_backupdel(self, cmd):
        """Delete a Tableau backup."""

        target = None
        if len(cmd.args) != 1:
            self.print_usage(self.do_backupdel.__usage__)
            return
        backup = cmd.args[0]

        aconn = self.get_aconn(cmd.dict)
        if not aconn:
            self.error(ERROR_AGENT_NOT_FOUND)
            return

        if not aconn.user_action_lock(blocking=False):
            self.error(ERROR_BUSY)
            return

        stateman = self.server.stateman
        main_state = stateman.get_state()
        if main_state in (StateManager.STATE_STARTED,
                                                StateManager.STATE_DEGRADED):
            stateman.update(StateManager.STATE_STARTED_BACKUPDEL)
        elif main_state == StateManager.STATE_STOPPED:
            stateman.update(StateManager.STATE_STOPPED_BACKUPDEL)
        else:
            self.error(ERROR_WRONG_STATE,
                                    "FAIL: Main state is %s." % (main_state))
            aconn.user_action_unlock()
            return

        self.ack()
        body = self.server.backupdel_cmd(backup)

        stateman.update(main_state)

        aconn.user_action_unlock()
        self.report_status(body)


    @usage('extract IMPORT')
    def do_extract(self, cmd):
        """Import extracts from the background_jobs table in Tableau"""

        # Reserved for later expansion
        if len(cmd.args) != 1 or cmd.args[0].upper() != 'IMPORT':
            self.print_usage(self.do_extract.__usage__)
            return

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        if not self.server.odbc_ok():
            self.error(ERROR_WRONG_STATE, "FAIL: Main state is %s." % \
                                            self.server.stateman.get_state())
            return

        self.ack()
        body = self.server.extract.load(agent)
        self.report_status(body)


    @usage('restore backup-name')
    def do_restore(self, cmd):
        """Restore. 
        The "name" is not a full path-name, but is the backup
        filename from the 'backup' table.
        """

        if len(cmd.args) != 1:
            self.print_usage(self.do_restore.__usage__)
            return

        backup_name = cmd.args[0]

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        aconn = agent.connection

        # lock to ensure against two simultaneous user actions
        if not aconn.user_action_lock(blocking=False):
            self.error(ERROR_BUSY)
            return

        # Check to see if we're in a state to restore
        stateman = self.server.stateman
        main_state = stateman.get_state()

        # Backups can be done when Tableau is either started, degraded
        # or stopped.
        if main_state not in (StateManager.STATE_STARTED,
                    StateManager.STATE_DEGRADED, StateManager.STATE_STOPPED):
            self.error(ERROR_WRONG_STATE,
                "FAIL: Can't backup before restore - main state is:", \
                                                                  main_state)
            self.server.log.debug("Can't backup before restore - main state is: %s",
                                                                    main_state)
            aconn.user_action_unlock()
            return

        reported_status = self.server.statusmon.get_reported_status()
        # The reported status from tableau needs to be running or stopped
        # to do a backup.  If it is, set our state to
        # STATE_*_BACKUP_RESTORE.
        if reported_status in (TableauProcess.STATUS_RUNNING,
                                        TableauProcess.STATUS_DEGRADED):
            stateman.update(StateManager.STATE_STARTED_BACKUP_RESTORE)
        elif reported_status == TableauProcess.STATUS_STOPPED:
            stateman.update(StateManager.STATE_STOPPED_BACKUP_RESTORE)
        else:
            self.error(ERROR_WRONG_STATE,
                "FAIL: Can't backup before restore - reported status is:", \
                                                              reported_status)
            self.server.log.debug(\
                "Can't backup before restore - reported status is: %s", \
                                                    reported_status)
            aconn.user_action_unlock()
            return

        # Do a backup before we try to do a restore.
        #FIXME: refactor do_backup() into do_backup() and backup()
        self.server.log.debug("------------Starting Backup for Restore--------------")
        if cmd.dict.has_key('userid'):
            userid = int(cmd.dict['userid'])
        else:
            userid = None

        self.server.event_control.gen( \
            EventControl.BACKUP_BEFORE_RESTORE_STARTED, agent.__dict__,
            userid=userid)

        self.ack()

        # Before we do anything, do a license check, which automatically
        # sends an event if appropriate.
        license_body = self.server.license(agent)
        if self.failed(license_body):
            stateman.update(main_state)
            self.report_status(license_body)
            aconn.user_action_unlock()
            return

        # No alerts or state updates are done in backup_cmd().
        body = self.server.backup_cmd(agent)

        if self.success(body):
            self.server.event_control.gen(\
                EventControl.BACKUP_BEFORE_RESTORE_FINISHED,
                dict(body.items() + agent.__dict__.items()),
                userid=userid)
        else:
            self.server.event_control.gen(\
                EventControl.BACKUP_BEFORE_RESTORE_FAILED,
                dict(body.items() + agent.__dict__.items()),
                userid=userid)

            self.report_status(body)
            stateman.update(main_state)
            aconn.user_action_unlock()
            return

        self.server.log.debug("-----------------Starting Restore-------------------")

        # restore_cmd() updates the state correctly depending on the
        # success of backup, copy, stop, restore, etc.
        body = self.server.restore_cmd(agent, backup_name, main_state,
                                                                userid=userid)

        # The final RESTORE_FINISHED/RESTORE_FAILED alert is sent only here and
        # not in restore_cmd().  Intermediate alerts like RESTORE_STARTED
        # are sent in restore_cmd().
        if self.success(body):
            # Restore finished successfully.  The main state has.
            # already been set.
            self.server.event_control.gen( \
                EventControl.RESTORE_FINISHED,
                dict(body.items() + agent.__dict__.items()),
                userid=userid)
        else:
            self.server.event_control.gen( \
                EventControl.RESTORE_FAILED,
                dict(body.items() + agent.__dict__.items()),
                userid=userid)

        # Get the latest status from tabadmin
        self.server.statusmon.check_status_with_connection(agent)
        # Don't unlock to allow the status thread to ALSO do
        # 'tabadmin status -v' until at least we finish with ours.
        aconn.user_action_unlock()

        self.report_status(body)

    @usage('copy source-agent-name:filename dest-agent-name dest-dir')
    def do_copy(self, cmd):
        """Copy a file from one agent to another."""

        if len(cmd.args) != 3:
            self.print_usage(self.do_copy.__usage__)
            return

        if self.server.upgrading():
            self.error(ERROR_WRONG_STATE, "Upgrading")
            return

        self.ack()
        body = self.server.copy_cmd(cmd.args[0], cmd.args[1], cmd.args[2])
        self.report_status(body)

    # FIXME: print status too
    def list_agents(self):
        session = meta.Session()
        agents = self.server.agentmanager.all_agents()

        if len(agents) == 0:
            self.report_status({'agents':[]})
            return

        # FIXME: print the agent state too.
        agent_dict_list = []
        for key in agents:
            agent = session.merge(agents[key])
            agent_dict_list.append(agent.todict())
        self.report_status({'agents': agent_dict_list})

    def list_backups(self):
        s = ''
        # FIXME: per environment
        backups = []
        for backup in BackupManager.all(self.server.domain.domainid):
            backups.append(backup.todict())
        self.report_status({'backups': backups})

    @usage('list [agents|backups]')
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
            self.print_usage(self.do_list.__usage__)
            return

        self.ack()
        f()

    @usage('cli <command> [args...]')
    def do_cli(self, cmd):
        if len(cmd.args) < 1:
            self.print_usage(self.do_cli.__usage__)
            return

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        self.ack()

        cli_command = cmd.args[0]
        for arg in cmd.args[1:]:
            if ' ' in arg:
                cli_command += ' "' + arg + '" '
            else:
                cli_command += ' ' + arg
        body = self.server.cli_cmd(cli_command, agent)
        self.report_status(body)

    @usage('phttp GET|PUT <URL> [source-or-destination]')
    def do_phttp(self, cmd):
        if len(cmd.args) < 2:
            self.print_usage(self.do_phttp.__usage__)
            return

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        if self.server.upgrading():
            self.error(ERROR_WRONG_STATE, "Upgrading")
            return

        self.ack()

        phttp_cmd = "phttp"
        for arg in cmd.args:
            if ' ' in arg:
                phttp_cmd += ' "' + arg + '"'
            else:
                phttp_cmd += ' ' + arg

        env = {u'BASIC_USERNAME': agent.username,
               u'BASIC_PASSWORD': agent.password}

        body = self.server.cli_cmd(phttp_cmd, agent, env=env)
        self.report_status(body)

    @usage('info [all]')
    def do_info(self, cmd):
        """Run pinfo."""
        if len(cmd.args) == 1:
            if cmd.args[0] != 'all':
                self.print_usage(self.do_info.__usage__)
                return
        elif len(cmd.args) > 2:
            self.print_usage(self.do_info.__usage__)
            return

        if not self.server.odbc_ok():
            self.error(ERROR_WRONG_STATE, "FAIL: Main state is %s." % \
                                        self.server.stateman.get_state())
            return

        if not len(cmd.args):
            agent = self.get_agent(cmd.dict)
            if not agent:
                return

            self.ack()
            body = self.server.get_pinfo(agent, update_agent=True)
            self.report_status(body)
            return

        self.ack()

        agents = self.server.agentmanager.all_agents()
        if len(agents) == 0:
            json.dumps({})
            return

        pinfos = []
        for key in agents.keys():
            try:
                agent = agents[key]
            except:
                # This agent is now gone
                continue

            body = self.server.get_pinfo(agent, update_agent=True)
            pinfos.append(body)

        self.report_status({"pinfos": pinfos})

    @usage('license')
    def do_license(self, cmd):
        """Run license check."""
        if len(cmd.args):
            self.print_usage(self.do_license.__usage__)
            return

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        if not self.server.odbc_ok():
            self.error(ERROR_WRONG_STATE, "FAIL: Main state is %s." % \
                                            self.server.stateman.get_state())
            return

        self.ack()
        d = self.server.license(agent)
        self.report_status(d)

    @usage('yml')
    def do_yml(self, cmd):
        if len(cmd.args):
            self.print_usage(self.do_yml.__usage__)
            return

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        if agent.agent_type != AgentManager.AGENT_TYPE_PRIMARY:
            self.error(AGENT_NOT_PRIMARY)
            return

        self.ack()
        body = self.server.yml(agent)
        self.report_status(body)

    @usage('sched [status | delete job-name [job-name ...] | ' + \
               'add min hour dom mon dow command ]\n' + \
               'Note: dow uses 0 for Monday while cron dow uses 0 for Sunday')
    def do_sched(self, cmd):
        """Manipulate scheduler."""
        if not len(cmd.args):
            self.print_usage(self.do_sched.__usage__)
            return

        if len(cmd.args) == 1 and cmd.args[0] == 'status':
            self.ack()
            body = self.server.sched.status()
        elif len(cmd.args) >= 1 and cmd.args[0][:3] == 'del':
            self.ack()
            body = self.server.sched.delete(cmd.args[1:])
        elif len(cmd.args) == 7 and cmd.args[0] == 'add':
            args = cmd.args[1:]
            body = self.server.sched.add(args[0], args[1], args[2], args[3],
                                                        args[4], args[5])
            if self.success(body):
                self.ack()
        else:
            self.print_usage(self.do_sched.__usage__)
            return

        if self.failed(body):
            self.error(ERROR_COMMAND_FAILED, str(body))
        else:
            self.report_status(body)
        return

    @usage('firewall { status | { enable | disable } port [port] }')
    def do_firewall(self, cmd):
        """Report the status of all ports or enable/disable one or more
           ports on an agent firewall."""

        if len(cmd.args) == 0:
                self.print_usage(self.do_firewall.__usage__)
                return
        elif len(cmd.args) == 1:
            if cmd.args[0] != "status":
                self.print_usage(self.do_firewall.__usage__)
                return
        elif cmd.args[0] not in ("enable", "disable"):
                self.print_usage(self.do_firewall.__usage__)
                return

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        if  cmd.args[0] != "status":
            ports = []
            try:
                ports = [int(cmd.args[i]) for i in range(1, len(cmd.args))]
            except ValueError, e:
                self.error(ERROR_INVALID_PORT,
                                    "firewall: Invalid port: " + str(e))
                return

        self.ack()

        if cmd.args[0] == "status":
            body = agent.firewall.status()
        elif cmd.args[0] == "enable":
            body = agent.firewall.enable(ports)
        elif cmd.args[0] == "disable":
            body = agent.firewall.disable(ports)

        self.report_status(body)
        return

    @usage('ping')
    def do_ping(self, cmd):
        """Ping an agent"""
        if len(cmd.args):
            self.print_usage(self.do_ping.__usage__)
            return

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

#        self.print_client("Sending ping to displayname '%s' (type: %s)." % \
#          (agent.displayname, agent.agent_type))

        body = self.server.ping(agent)
        self.report_status(body)

    @usage('start')
    def do_start(self, cmd):
        if len(cmd.args) != 0:
            self.print_usage(self.do_start.__usage__)
            return

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        aconn = agent.connection
        # lock to ensure against two simultaneous user actions
        if not aconn.user_action_lock(blocking=False):
            self.error(ERROR_BUSY)
            return

        # Check to see if we're in a state to start
        stateman = self.server.stateman
        main_state = stateman.get_state()

        # Start can be done only when Tableau is stopped.
        if main_state != StateManager.STATE_STOPPED:
            self.error(ERROR_WRONG_STATE,
                                "Can't start - main state is: " + main_state)
            aconn.user_action_unlock()
            return

        reported_status = self.server.statusmon.get_reported_status()
        if reported_status != TableauProcess.STATUS_STOPPED:
            self.error(ERROR_WRONG_STATE,
                        "Can't start - reported status is: " + reported_status)
            aconn.user_action_unlock()
            return

        stateman.update(StateManager.STATE_STARTING)

        self.server.log.debug("-----------------Starting Tableau-------------------")
        # fixme: Reply with "OK" only after the agent received the command?
        self.ack()

        if cmd.dict.has_key('userid'):
            userid = int(cmd.dict['userid'])
        else:
            userid = None

        # Stop the maintenance web server and relinquish the web
        # server port before tabadmin start tries to listen on the web
        # server port.
        maint_body = self.server.maint("stop")
        # let it continue ?

        body = self.server.cli_cmd('tabadmin start', agent)
        if body.has_key("exit-status"):
            exit_status = body['exit-status']
        else:
            exit_status = 1 # if no 'exit-status' then consider it failed.

        if exit_status:
            # The "tableau start" failed.  Go back to "STOPPED" state.
            self.server.event_control.gen( \
                EventControl.TABLEAU_START_FAILED,
                dict(body.items() + agent.__dict__.items()),
                userid=userid)
            stateman.update(StateManager.STATE_STOPPED)
            self.server.event_control.gen( \
                EventControl.STATE_STOPPED, agent.__dict__,
                userid=userid)
        else:
            stateman.update(StateManager.STATE_STARTED)
            self.server.event_control.gen( \
                EventControl.STATE_STARTED, agent.__dict__,
                userid=userid)

        # Get the latest status from tabadmin
        self.server.statusmon.check_status_with_connection(agent)

        aconn.user_action_unlock()
        # STARTED is set by the status monitor since it really knows the status.
        self.report_status(body)

    @usage('stop [no-backup|nobackup] [no-license|nolicense]')
    def do_stop(self, cmd):

        backup_first = True
        license_check = True

        for arg in cmd.args:
            arg = arg.lower()
            if arg == "no-backup" or arg == "nobackup":
                backup_first = False
            elif arg == "no-license" or arg == "nolicense":
                license_check = False
            else:
                self.print_usage(self.do_stop.__usage__)
                return

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        aconn = agent.connection

        # lock to ensure against two simultaneous user actions
        if not aconn.user_action_lock(blocking=False):
            self.error(ERROR_BUSY)
            return

        # Check to see if we're in a state to stop
        stateman = self.server.stateman
        main_state = stateman.get_state()

        # Stop can be done only if tableau is started
        if main_state not in \
                (StateManager.STATE_STARTED, StateManager.STATE_DEGRADED):
            self.error(ERROR_WRONG_STATE,
                                "can't stop - main state is: " + main_state)
            aconn.user_action_unlock()
            return

        reported_status = self.server.statusmon.get_reported_status()
        if reported_status not in (TableauProcess.STATUS_RUNNING,
                                            TableauProcess.STATUS_DEGRADED):
            self.error(ERROR_WRONG_STATE,
                        "FAIL: Can't start - reported status is: %s",
                                                              reported_status)
            self.server.log.debug("Can't start - reported status is: %s",
                                                                reported_status)
            aconn.user_action_unlock()
            return

        self.ack()
        # Before we do anything, do a license check, which automatically
        # sends an event if appropriate.
        if license_check:
            license_body = self.server.license(agent)
            if self.failed(license_body):
                stateman.update(main_state)
                self.report_status(license_body)
                aconn.user_action_unlock()
                return

        if cmd.dict.has_key('userid'):
            userid = int(cmd.dict['userid'])
        else:
            userid = None

        if backup_first:
            self.server.log.debug(\
                        "------------Starting Backup for Stop---------------")
            stateman.update(StateManager.STATE_STARTED_BACKUP_STOP)
            self.server.event_control.gen( \
                EventControl.BACKUP_BEFORE_STOP_STARTED, agent.__dict__,
                userid=userid)

            body = self.server.backup_cmd(agent)

            if self.success(body):
                self.server.event_control.gen( \
                    EventControl.BACKUP_BEFORE_STOP_FINISHED,
                    dict(body.items() + agent.__dict__.items()),
                    userid=userid)
            else:
                self.server.event_control.gen( \
                    EventControl.BACKUP_BEFORE_STOP_FAILED,
                    dict(body.items() + agent.__dict__.items()),
                    userid=userid)

                # Backup failed.  Will not attempt stop
                msg = 'Backup failed.  Will not attempt stop'
                if 'info' in body:
                    body['info'] += '\n' + msg
                else:
                    body['info'] = msg
                self.report_status(body)
                aconn.user_action_unlock()
                return

        # Note: Make sure to set the state in the database before
        # we report "OK" back to the client since "OK" to the UI client
        # results in an immediate check of the state.
        stateman.update(StateManager.STATE_STOPPING)

        # FIXME: end backup

        self.server.log.debug("-----------------Stopping Tableau-------------------")
        # fixme: Reply with "OK" only after the agent received the command?

        body = self.server.cli_cmd('tabadmin stop', agent)
        if self.success(body):
            # Start the maintenance server only after Tableau has stopped
            # and reqlinquished the web server port.
            maint_body = self.server.maint("start")
            if self.failed(maint_body):
                msg = "maint start failed: " + str(maint_body)
                if not 'info' in body:
                    body['info'] = msg
                else:
                    body['info'] += "\n" + msg

        # We set the state to stop, even though the stop failed.
        # This will be corrected by the 'tabadmin status -v' processing
        # later.
        stateman.update(StateManager.STATE_STOPPED)
        self.server.event_control.gen( \
            EventControl.STATE_STOPPED, agent.__dict__,
            userid=userid)

        # Get the latest status from tabadmin which sets the main state.
        self.server.statusmon.check_status_with_connection(agent)

        # If the 'stop' had failed, set the status to what we just
        # got back from 'tabadmin status ...'
        if self.failed(body):
            reported_status = self.server.statusmon.get_reported_status()
            stateman.update(reported_status)

        aconn.user_action_unlock()

        # fixme: check & report status to see if it really stopped?
        self.report_status(body)

    @usage('maint [start|stop]')
    def do_maint(self, cmd):
        """Start or Stop the maintenance webserver on the agent."""

        if len(cmd.args) < 1 or len(cmd.args) > 2:
            self.print_usage(self.do_maint.__usage__)
            return

        action = cmd.args[0].lower()
        if action != "start" and action != "stop":
            self.print_usage(self.do_maint.__usage__)
            return

        port = -1
        if len(cmd.args) == 2:
            try:
                port = int(cmd.args[1])
            except ValueError, e:
                self.error(ERROR_INVALID_PORT,
                            "invalid port '%s', number required.", cmd.args[1])
                return;

        self.ack()

        body = self.server.maint(action, port)
        self.report_status(body)

    @usage('archive [start|stop] [port]')
    def do_archive(self, cmd):
        """Start or Stop the archive HTTPS server on the agent."""
        if len(cmd.args) < 1 or len(cmd.args) > 2:
            self.print_usage(self.do_archive.__usage__)
            return

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        action = cmd.args[0].lower()
        if action != "start" and action != "stop":
            self.print_usage(self.do_archive.__usage__)
            return

        port = -1
        if len(cmd.args) == 2:
            try:
                port = int(cmd.args[1])
            except ValueError, e:
                self.error(ERROR_INVALID_PORT,
                        "invalid port '%s', number required.", cmd.args[1])
                return;

        self.ack()

        body = self.server.archive(agent, action, port)
        self.report_status(body)


    @usage('displayname new-displayname')
    def do_displayname(self, cmd):
        """Set the display name for an agent"""
        if len(cmd.args) != 1:
            self.print_usage(self.do_displayname.__usage__)
            return

        new_displayname = cmd.args[0]
        uuid = cmd.dict['uuid']

        # Note: aconn will be None if agent is not connected, which is OK
        aconn = self.server.agentmanager.agent_conn_by_uuid(uuid)

        try:
            self.server.displayname_cmd(aconn, uuid, new_displayname)
            self.ack()
        except ValueError, e:
            self.error(ERROR_COMMAND_FAILED, str(e))

        body = {}
        self.report_status(body)


    @usage('file [GET|PUT|DELETE|SHA256|MOVE|LISTDIR|SIZE|MKDIRS|WRITE] <path> [arg]')
    def do_file(self, cmd):
        """Manipulate a particular file on the agent."""

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        if len(cmd.args) < 2 or len(cmd.args) > 3:
            self.print_usage(self.do_file.__usage__)
            return

        method = cmd.args[0].upper()
        path = cmd.args[1]

        try:
            if method == 'GET':
                if len(cmd.args) != 3:
                    self.print_usage(self.do_file.__usage__)
                    return
                self.ack()
                body = agent.filemanager.save(path, cmd.args[2])
            elif method == 'PUT':
                if len(cmd.args) != 3:
                    self.print_usage(self.do_file.__usage__)
                    return
                self.ack()
                body = agent.filemanager.sendfile(path, cmd.args[2])
            elif method == 'DELETE':
                if len(cmd.args) != 2:
                    self.print_usage(self.do_file.__usage__)
                    return
                self.ack()
                agent.filemanager.delete(path)
                body = {}
            elif method == 'SHA256':
                if len(cmd.args) != 2:
                    self.print_usage(self.do_file.__usage__)
                    return
                self.ack()
                body = agent.filemanager.sha256(path)
            elif method == 'MOVE':
                if len(cmd.args) != 3:
                    self.print_usage(self.do_file.__usage__)
                    return
                self.ack()
                body = agent.filemanager.move(path, cmd.args[2])
            elif method == 'LISTDIR':
                if len(cmd.args) != 2:
                    self.print_usage(self.do_file.__usage__)
                    return
                self.ack()
                body = agent.filemanager.listdir(path)
            elif method == 'MKDIRS':
                if len(cmd.args) != 2:
                    self.print_usage(self.do_file.__usage__)
                    return
                self.ack()
                body = agent.filemanager.mkdirs(path)
            elif method == 'FILESIZE' or method == 'SIZE':
                if len(cmd.args) != 2:
                    self.print_usage(self.do_file.__usage__)
                    return
                self.ack()
                body = agent.filemanager.filesize(path)
            elif method == "WRITE":
                self.ack()
                agent.filemanager.put(path, cmd.args[2])
                body = {}
            else:
                self.print_usage(self.do_file.__usage__)
                return
        except exc.HTTPException, e:
            body = {'error': 'HTTP Failure',
                 'status-code': e.status,
                 'reason-phrase': e.reason,
                 }
            if e.method:
                body['method'] = e.method
            if e.body:
                body['body'] = e.body

        self.report_status(body)

    @usage('hup')
    def do_hup(self, cmd):
        """Make an agent restart itself."""
        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        self.ack()
        agent.connection.http_send_json("/hup", {})
        self.report_status({})

    @usage('s3 [GET|PUT] <name> <key-or-path>')
    def do_s3(self, cmd):
        """Send a file to or receive a file from an S3 bucket"""

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        aconn = agent.connection
        if len(cmd.args) != 3 or len(cmd.args) > 4:
            self.print_usage(self.do_s3.__usage__)
            return

        action = cmd.args[0].upper()
        name = cmd.args[1]
        keypath = cmd.args[2]

        entry = self.server.s3.get_by_name(name)
        if not entry:
            self.error(ERROR_NOT_FOUND, "s3 instance '" + name + "' not found.")
            return

        data_dir = self.server.backup.primary_data_loc_path(agent)

        if not data_dir:
            self.error(ERROR_NOT_FOUND,
                        "Missing primary-data_loc in the agent_volumes table")
            return

        self.ack()

        resource = os.path.basename(keypath)
        token = entry.get_token(resource)

        command = 'ps3 %s %s "%s"' % \
            (action, entry.bucket, keypath)

        # fixme: this method doesn't work
        env = {u'ACCESS_KEY': token.credentials.access_key,
               u'SECRET_KEY': token.credentials.secret_key,
               u'SESSION': token.credentials.session_token,
               u'REGION_ENDPOINT': entry.region,
               u'PWD': data_dir}

        env = {u'ACCESS_KEY': entry.access_key,
               u'SECRET_KEY': entry.secret,
               u'PWD': data_dir}

        # Send command to the agent
        body = self.server.cli_cmd(command, agent, env=env)

        body[u'env'] = env
        body[u'resource'] = resource

        self.report_status(body)

    @usage('gcs [GET|PUT] gcs-ame key-or-path')
    def do_gcs(self, cmd):
        """Send a file to or receive a file from a GCP bucket"""

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        aconn = agent.connection
        if len(cmd.args) != 3 or len(cmd.args) > 4:
            self.print_usage(self.do_gcs.__usage__)
            return

        action = cmd.args[0].upper()
        name = cmd.args[1]
        keypath = cmd.args[2]

        entry = self.server.gcs.get_by_name(name)
        if not entry:
            self.error(ERROR_NOT_FOUND,
                                    "gcs instance '" + name + "' not found.")
            return

        data_dir = self.server.backup.primary_data_loc_path(agent)

        if not data_dir:
            self.error(ERROR_NOT_FOUND,
                        "Missing primary-data_loc in the agent_volumes table")
            return

        self.ack()

        resource = os.path.basename(keypath)

        command = 'pgcs %s %s "%s"' % \
            (action, entry.bucket, keypath)

        # FIXME: We don't really want to send our real keys and
        #        secrets to the agents, but while boto.connect_gs
        #        can replace boto.connect_s3, there is no GCS
        #        equivalent for boto.connect_sts, so we may need
        #        to move away from boto to get GCS temporary tokens.
        env = {u'ACCESS_KEY': entry.access_key,
               u'SECRET_KEY': entry.secret,
               u'PWD': data_dir}

        # Send command to the agent
        body = self.server.cli_cmd(command, agent, env=env)

        body[u'env'] = env
        body[u'resource'] = resource

        self.report_status(body)

    @usage('sql <statement>')
    def do_sql(self, cmd):
        """Run a SQL statement against the Tableau database."""

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        # FIXME: check for primary agent

        if len(cmd.args) != 1:
            self.print_usage(self.do_sql.__usage__)
            return

        if not self.server.odbc_ok():
            self.error(ERROR_WRONG_STATE, "FAIL: Main state is %s." % \
                                            self.server.stateman.get_state())
            return

        stmt = cmd.args[0]
        self.ack()

        body = agent.odbc.execute(stmt)
        self.report_status(body)

    @usage('auth [import|verify] <username> <password>')
    def do_auth(self, cmd):
        """Work with the Tableau user data."""

        if len(cmd.args) < 1:
            self.print_usage(self.do_auth.__usage__)
            return

        action = cmd.args[0].lower()

        if not self.server.odbc_ok():
            self.error(ERROR_WRONG_STATE, "FAIL: Main state is %s." % \
                                            self.server.stateman.get_state())
            return

        if action == 'import':
            if len(cmd.args) != 1:
                self.print_usage(self.do_auth.__usage__)
                return
            agent = self.get_agent(cmd.dict)
            if not agent:
                return
            self.ack()
            body = self.server.auth.load(agent)
        elif action == 'verify':
            if len(cmd.args) != 3:
                self.print_usage(self.do_auth.__usage__)
                return
            self.ack()
            result = self.server.auth.verify(cmd.args[1], cmd.args[2])
            body = {u'status': result and 'OK' or 'INVALID'}
        else:
            self.print_usage(self.do_auth.__usage__)
            return
        self.report_status(body)

    @usage('ad verify <username> <password>')
    def do_ad(self, cmd):
        """Authenticate against Active Directory."""

        if len(cmd.args) < 1:
            self.print_usage(self.do_ad.__usage__)
            return

        action = cmd.args[0].lower()
        if action == 'verify':
            if len(cmd.args) != 3:
                self.print_usage(self.do_ad.__usage__)
                return
            agent = self.get_agent(cmd.dict)
            if not agent:
                return
            self.ack()
            body = self.server.active_directory_verify(agent,
                                                       cmd.args[1],
                                                       cmd.args[2])
        else:
            self.print_usage(self.do_ad.__usage__)
            return
        self.report_status(body)

    @usage('sync')
    def do_sync(self, cmd):
        """Synchronize Tableau tables."""

        if len(cmd.args) != 0:
            self.print_usage(self.do_sync.__usage__)
            return

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        if not self.server.odbc_ok():
            self.error(ERROR_WRONG_STATE, "FAIL: Main state is %s." % \
                                            self.server.stateman.get_state())
            return

        self.ack()

        body = self.server.sync_cmd(agent)

        if self.failed(body):
            self.error(ERROR_COMMAND_FAILED, str(body))
        else:
            self.print_client("%s", json.dumps(body))

    @usage('system <SET|GET|DELETE> <key> [value]')
    def do_system(self, cmd):
        """ Set or Delete a 'system' table entry for the current environment."""
        value = None
        body = {}

        if len(cmd.args) < 1:
            self.print_usage(self.do_system.__usage__)
            return

        action = cmd.args[0].upper()
        if action == 'SET':
            if len(cmd.args) != 3:
                self.print_usage(self.do_system.__usage__)
                return
            value = cmd.args[2]
        elif action == 'GET':
            if len(cmd.args) != 2:
                self.print_usage(self.do_system.__usage__)
                return
        elif action == 'DELETE':
            if len(cmd.args) != 2:
                self.print_usage(self.do_system.__usage__)
                return
        else:
            self.print_usage(self.do_system.__usage__)
            return

        self.ack()

        key = cmd.args[1]

        entry = None
        try:
            entry = self.server.system.entry(key)
        except ValueError:
            pass

        session = meta.Session()
        if action == 'SET':
            if entry:
                entry.value = value
            else:
                entry = SystemEntry(envid=self.server.environment.envid,
                                    key=key, value=value)
                session.add(entry)
            body['status'] = 'OK'
        elif action == 'GET':
            if not entry:
                body['error'] = 'Key not found'
            else:
                body['key'] = entry.key
                body['value'] = entry.value
        elif action == 'DELETE':
            if entry:
                session.delete(entry)
            body['status'] = 'OK'
        session.commit()
        return self.report_status(body)

    @usage('ziplogs')
    def do_ziplogs(self, cmd):
        """Run 'tabadmin ziplogs'."""

        target = None
        if len(cmd.args) != 0:
            self.print_usage(self.do_ziplogs.__usage__)
            return

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        aconn = agent.connection
        if not aconn.user_action_lock(blocking=False):
            self.error(ERROR_WRONG_STATE)
            return

        stateman = self.server.stateman
        main_state = stateman.get_state()
        if main_state in (StateManager.STATE_STARTED,
                                                StateManager.STATE_DEGRADED):
            stateman.update(StateManager.STATE_STARTED_ZIPLOGS)
        elif main_state == StateManager.STATE_STOPPED:
            stateman.update(StateManager.STATE_STOPPED_ZIPLOGS)
        else:
            self.error(ERROR_WRONG_STATE,
                                    "FAIL: Main state is %s." % (main_state))
            aconn.user_action_unlock()
            return

        # FIXME: Do we want to send alerts?
        #server.event_control.gen(EventControl.BACKUP_STARTED)
        self.ack()

        body = self.server.ziplogs_cmd(agent)

        stateman.update(main_state)
        aconn.user_action_unlock();

        self.report_status(body)
        if self.success(body):
            # FIXME: Do we want to send alerts?
            #server.event_control.gen(EventControl.ZIPLOGS_FINISHED, 
            #                    dict(body.items() + agent.__dict__.items()))
            pass
        else:
            # FIXME: Do we want to send alerts?
            #server.event_control.gen(EventControl.ZIPLOGS_FAILED,
            #                    dict(body.items() + agent.__dict__.items()))
            pass

    @usage('cleanup')
    def do_cleanup(self, cmd):
        """Run 'tabadmin cleanup'."""

        target = None
        if len(cmd.args) != 0:
            self.print_usage(self.do_cleanup.__usage__)
            return

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        aconn = agent.connection
        if not aconn.user_action_lock(blocking=False):
            self.error(ERROR_BUSY)
            return

        stateman = self.server.stateman
        main_state = stateman.get_state()
        if main_state in (StateManager.STATE_STARTED,
                                        StateManager.STATE_DEGRADED):
            stateman.update(StateManager.STATE_STARTED_CLEANUP)
        elif main_state == StateManager.STATE_STOPPED:
            stateman.update(StateManager.STATE_STOPPED_CLEANUP)
        else:
            self.error(ERROR_WRONG_STATE,
                                "FAIL: Main state is %s." % (main_state))
            aconn.user_action_unlock()
            return

        # FIXME: Do we want to send alerts?
        #server.event_control.gen(EventControl.BACKUP_STARTED)
        self.ack()

        body = self.server.cleanup_cmd(agent)

        stateman.update(main_state)
        aconn.user_action_unlock();

        self.report_status(body)
        if self.success(body):
            # FIXME: Do we want to send alerts?
            #server.event_control.gen(EventControl.CLEANUP_FINISHED,
            #                    dict(body.items() + agent.__dict__.items()))
            pass
        else:
            # FIXME: Do we want to send alerts?
            #server.event_control.gen(EventControl.CLEANUP_FAILED,
            #                    dict(body.items() + agent.__dict__.items()))
            pass

    @usage('nop')
    def do_nop(self, cmd):
        self.ack()

        body = {'dict': cmd.dict,
                'command': cmd.name,
                'args': cmd.args}

        self.report_status(body)

    def get_agent(self, opts, error_on_no_agent=True):
        agent = None

        if opts.has_key('uuid'): # should never fail
            uuid = opts['uuid'] # may be None
            if uuid:
                agent = self.server.agentmanager.agent_by_uuid(uuid)
                if not agent and error_on_no_agent:
                    self.error(ERROR_AGENT_NOT_CONNECTED,
                                    "No connected agent with uuid=%s" % (uuid))
            elif error_on_no_agent:
                self.error(ERROR_AGENT_NOT_SPECIFIED)
        else: # should never happen
            if error_on_no_agent:
                self.error(ERROR_AGENT_NOT_SPECIFIED)

        return agent

    # DEPRECATED
    def get_aconn(self, opts):
        # FIXME: This method is a temporary hack while we
        #        clean up the telnet commands
        # FIXME: TBD: Should this be farmed out to another class?
        agent = self.get_agent(opts)
        return agent and agent.connection or None

    def handle(self):
        while True:
            try:
                data = self.rfile.readline().strip()
            except socket.error as e:
                self.error(ERROR_SOCKET_DISCONNECTED,
                    "CliHandler: telnet client socket failure/disconnect: " + \
                                                                        str(e))
                break

            if not data: break

            self.server.log.debug("telnet command: '%s'", data)

            try:
                cmd = Command(self.server, data)
            except CommandException, e:
                self.error(ERROR_COMMAND_SYNTAX_ERROR, str(e))
                continue
            except Exception, e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                tb = ''.join(traceback.format_tb(exc_traceback)).\
                                                        replace('\n', '')
                line = "cmd: %s.  Traceback: %s" % (sys.exc_info()[1], tb)

                self.error(ERROR_COMMAND_FAILED, line)

            if not hasattr(self, 'do_'+cmd.name):
                self.error(ERROR_NO_SUCH_COMMAND,
                                            'invalid command: %s', cmd.name)
                continue

            # <command> /displayname=X /type=primary, /uuid=Y, /hostname=Z [args]
            session = meta.Session()
            try:
                f = getattr(self, 'do_'+cmd.name)
                f(cmd)
            # fixme on exceptions: reset state?
            except exc.InvalidStateError, e:
                self.error(ERROR_WRONG_STATE, e.message)
            except (IOError, ValueError) as e:
                self.error(ERROR_COMMAND_FAILED, "%s", str(e))
            except Exception, e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                tb = ''.join(traceback.format_tb(exc_traceback))
                                                        
                line = "%s.  Traceback: %s" % (sys.exc_info()[1],
                                                            tb.replace('\n', ''))

                self.error(ERROR_COMMAND_FAILED, line)
                self.server.log.error("Error: %s.  Traceback: %s" % \
                                                        (sys.exc_info()[1], tb))
            finally:
                session.rollback()
                meta.Session.remove()

