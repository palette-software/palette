import copy
import inspect
import os
import shlex
import SocketServer as socketserver
import socket

import ntpath

import sqlalchemy

from akiri.framework.ext.sqlalchemy import meta

from agent import Agent
from agentmanager import AgentManager
from backup import BackupManager
from event_control import EventControl
from s3 import S3
from system import SystemEntry
from state import StateManager
from tableau import TableauProcess

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

    def print_usage(self, msg):
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
        print >> self.wfile, '    /displayname=name /hostname=name ' + \
                                                    '/uuid=uuid /type=type'
        for name, m in inspect.getmembers(self, predicate=inspect.ismethod):
            if name.startswith("do_"):
                name = name[3:].replace('_', '-')
                print >> self.wfile, '  ' + name
                if m.__doc__:
                    print >> self.wfile, '    ' + m.__doc__
                if hasattr(m, '__usage__'):
                    print >> self.wfile, '    usage: ' + m.__usage__
        print >> self.wfile

    @usage('status')
    def do_status(self, cmd):
        if len(cmd.args):
            self.error("'status' does not have an argument.")
            self.print_usage(self.do_status.__usage__)
            return

        agent = self.get_agent(cmd.dict)
        if not agent:
            self.error('agent not found')
            return

        self.ack()
        body = self.server.cli_cmd("tabadmin status -v", agent)
        self.print_client(str(body))

    @usage('backup [target-displayname [volume-name]]')
    def do_backup(self, cmd):
        """Perform a Tableau backup and potentially migrate."""

        target = None
        volume_name = None

        if len(cmd.args) > 2:
            self.print_usage(self.do_backup.__usage__)
            return
        elif len(cmd.args) == 1:
            target = cmd.args[0]
        elif len(cmd.args) == 2:
            target = cmd.args[0]
            volume_name = cmd.args[1]

        agent = self.get_agent(cmd.dict)
        if not agent:
            self.error('agent not found')
            return

        aconn = agent.connection

        # lock to ensure against two simultaneous user actions
        if not aconn.user_action_lock(blocking=False):
            print >> self.wfile, "FAIL: Busy with another user request."
            return

        # Check to see if we're in a state to backup
        stateman = self.server.stateman
        main_state = stateman.get_state()

        # Backups can be done when Tableau is either started or stopped.
        if main_state not in \
                        (StateManager.STATE_STARTED, StateManager.STATE_STOPPED):
            print >> self.wfile, "FAIL: Can't backup - main state is:", \
                                                                  main_state
            self.server.log.debug("Can't backup - main state is: %s",  main_state)
            aconn.user_action_unlock()
            return

        reported_status = self.server.statusmon.get_reported_status()
        # The reported status from tableau needs to be running or stopped
        # to do a backup.
        if reported_status == TableauProcess.STATUS_RUNNING:
            stateman.update(StateManager.STATE_STARTED_BACKUP)
        elif reported_status == TableauProcess.STATUS_STOPPED:
            stateman.update(StateManager.STATE_STOPPED_BACKUP)
        else:
            #FIXME
            print >> self.wfile, "FAIL: Can't backup - reported status is:", \
                                                              reported_status
            self.server.log.debug("Can't backup - reported status is:", \
                                                            reported_status)
            aconn.user_action_unlock()
            return

        self.server.log.debug("-----------------Starting Backup-------------------")

        self.server.event_control.gen(EventControl.BACKUP_STARTED,
                                      agent.__dict__)

        self.ack()

        body = self.server.backup_cmd(agent, target, volume_name)

        self.print_client("%s", str(body))
        if not body.has_key('error'):
            self.server.event_control.gen(EventControl.BACKUP_FINISHED,
                        dict(body.items() + agent.__dict__.items()))
        else:
            self.server.event_control.gen(EventControl.BACKUP_FAILED,
                        dict(body.items() + agent.__dict__.items()))

        if reported_status == TableauProcess.STATUS_RUNNING:
            stateman.update(StateManager.STATE_STARTED)
        elif reported_status == TableauProcess.STATUS_STOPPED:
            stateman.update(StateManager.STATE_STOPPED)

        # Get the latest status from tabadmin
        self.server.statusmon.check_status_with_connection(agent)
        # Don't unlock to allow the status thread to ALSO do
        # 'tabadmin status -v' until at least we finish with ours.
        aconn.user_action_unlock()

    @usage('backupdel backup-name')
    def do_backupdel(self, cmd):
        """Delete a Tableau backup."""

        target = None
        if len(cmd.args) != 1:
            self.print_usage(self.do_backup.__usage__)
            return
        backup = cmd.args[0]

        aconn = self.get_aconn(cmd.dict)
        if not aconn:
            self.error('agent not found.')
            return

        if not aconn.user_action_lock(blocking=False):
            print >> self.wfile, "FAIL: Busy with another user request."
            return

        stateman = self.server.stateman
        main_state = stateman.get_state()
        if main_state == StateManager.STATE_STARTED:
            stateman.update(StateManager.STATE_STARTED_BACKUPDEL)
        elif main_state == StateManager.STATE_STOPPED:
            stateman.update(StateManager.STATE_STOPPED_BACKUPDEL)
        else:
            print >> self.wfile, "FAIL: Main state is %s." % (main_state)
            aconn.user_action_unlock()
            return

        self.ack()
        body = self.server.backupdel_cmd(backup)
        self.print_client("%s", str(body))

        stateman.update(main_state)

        aconn.user_action_unlock()

    @usage('extract IMPORT')
    def do_extract(self, cmd):
        """Import extracts from the background_jobs table in Tableau"""

        # Reserved for later expansion
        if len(cmd.args) != 1 or cmd.args[0].upper() != 'IMPORT':
            self.print_usage(self.do_extract.__usage__)
            return

        agent = self.get_agent(cmd.dict)
        if not agent:
            self.error('agent not found')
            return

        body = self.server.extract.load(agent)
        self.print_client("%s", str(body))

    @usage('restore [source:pathname]')
    def do_restore(self, cmd):
        """Restore.  If the file/path we are restoring from is on a different
        machine than the Primary Agent, then get the file/path to the
        Primary Agent first."""

        if len(cmd.args) != 1:
            self.print_usage(self.do_restore.__usage__)
            return

        target = cmd.args[0]

        agent = self.get_agent(cmd.dict)
        if not agent:
            self.error('agent not found')
            return

        aconn = agent.connection

        # lock to ensure against two simultaneous user actions
        if not aconn.user_action_lock(blocking=False):
            print >> self.wfile, "FAIL: Busy with another user request."
            return

        # Check to see if we're in a state to restore
        stateman = self.server.stateman
        main_state = stateman.get_state()

        # Backups can be done when Tableau is either started or stopped.
        if main_state not in \
                        (StateManager.STATE_STARTED, StateManager.STATE_STOPPED):
            print >> self.wfile,\
                "FAIL: Can't backup before restore - main state is:", \
                                                                  main_state
            self.server.log.debug("Can't backup before restore - main state is: %s",
                                                                    main_state)
            aconn.user_action_unlock()
            return

        reported_status = self.server.statusmon.get_reported_status()
        # The reported status from tableau needs to be running or stopped
        # to do a backup.  If it is, set our state to
        # STATE_*_BACKUP_RESTORE.
        if reported_status == TableauProcess.STATUS_RUNNING:
            stateman.update(StateManager.STATE_STARTED_BACKUP_RESTORE)
        elif reported_status == TableauProcess.STATUS_STOPPED:
            stateman.update(StateManager.STATE_STOPPED_BACKUP_RESTORE)
        else:
            print >> self.wfile, \
                "FAIL: Can't backup before restore - reported status is:", \
                                                              reported_status
            self.server.log.debug("Can't backup before restore - reported status is:", \
                                                            reported_status)
            aconn.user_action_unlock()
            return

        # Do a backup before we try to do a restore.
        #FIXME: refactor do_backup() into do_backup() and backup()
        self.server.log.debug("------------Starting Backup for Restore--------------")

        self.server.event_control.gen( \
            EventControl.BACKUP_BEFORE_RESTORE_STARTED, agent.__dict__)

        self.ack()

        # No alerts or state updates are done in backup_cmd().
        body = self.server.backup_cmd(agent)

        if not body.has_key('error'):
            self.server.event_control.gen(\
                EventControl.BACKUP_BEFORE_RESTORE_FINISHED,
                dict(body.items() + agent.__dict__.items()))
            backup_success = True
        else:
            self.server.event_control.gen(\
                EventControl.BACKUP_BEFORE_RESTORE_FAILED,
                dict(body.items() + agent.__dict__.items()))
            backup_success = False

        if not backup_success:
            self.print_client("Backup failed.  Aborting restore.")
            stateman.update(main_state)
            aconn.user_action_unlock()
            return

        self.server.log.debug("-----------------Starting Restore-------------------")

        # restore_cmd() updates the state correctly depending on the
        # success of backup, copy, stop, restore, etc.
        body = self.server.restore_cmd(agent, target, main_state)

        # The final RESTORE_FINISHED/RESTORE_FAILED alert is sent only here and
        # not in restore_cmd().  Intermediate alerts like RESTORE_STARTED
        # are sent in restore_cmd().
        if not body.has_key('error'):
            # Restore finished successfully.  The main state has.
            # already been set.
            self.server.event_control.gen( \
                EventControl.RESTORE_FINISHED,
                dict(body.items() + agent.__dict__.items()))
        else:
            self.server.event_control.gen( \
                EventControl.RESTORE_FAILED,
                dict(body.items() + agent.__dict__.items()))

        self.print_client(str(body))

        # Get the latest status from tabadmin
        self.server.statusmon.check_status_with_connection(agent)
        # Don't unlock to allow the status thread to ALSO do
        # 'tabadmin status -v' until at least we finish with ours.
        aconn.user_action_unlock()

    @usage('copy source-agent-name:filename dest-agent-name')
    def do_copy(self, cmd):
        """Copy a file from one agent to another."""

        if len(cmd.args) != 2:
            self.error(self.do_copy.__usage__)
            return

        body = self.server.copy_cmd(cmd.args[0], cmd.args[1])
        self.report_status(body)


    # FIXME: print status too
    def list_agents(self):
        agents = self.server.agentmanager.all_agents()

        if len(agents) == 0:
            self.print_client('{}')
            return

        # FIXME: print the agent state too.
        s = ''
        for key in agents:
            d = copy.copy(agents[key].connection.auth)
            d['displayname'] = agents[key].displayname
            s += str(d) + '\n'
        self.print_client(s)


    def list_backups(self):
        s = ''
        # FIXME: per environment
        for backup in BackupManager.all(self.server.domain.domainid):
            s += str(backup.todict()) + '\n'
        self.print_client(s)

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
            return self.error(self.do_cli.__usage__)
            return

        agent = self.get_agent(cmd.dict)
        if not agent:
            self.error('agent not found')
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

    @usage('phttp GET https://vol1/filename vol2:/local-directory')
    def do_phttp(self, cmd):
        if len(cmd.args) < 2:
            self.error(self.do_phttp.__usage__)
            return

        agent = self.get_agent(cmd.dict)
        if not agent:
            self.error('agent not found')
            return

        phttp_cmd = Controller.PHTTP_BIN
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

        if not len(cmd.args):
            agent = self.get_agent(cmd.dict)
            if not agent:
                self.error('agent not found')
                return

            self.ack()
            body = self.server.info(agent)
            self.print_client(str(body))
            return

        self.ack()

        agents = self.server.agentmanager.all_agents()
        if len(agents) == 0:
            self.print_client("{}")
            return

        pinfos = []
        for uuid, agent in agents.iteritems():
            body = self.server.info(agent)
            pinfos.append(body)

        self.print_client(str(pinfos))

    @usage('license')
    def do_license(self, cmd):
        """Run license check."""
        if len(cmd.args):
            self.print_usage(self.do_info.__usage__)
            return

        agent = self.get_agent(cmd.dict)
        if not agent:
            self.error('agent not found')
            return

        self.ack()
        d = self.server.license(agent)
        self.print_client(str(d))

    @usage('yml')
    def do_yml(self, cmd):
        if len(cmd.args):
            self.print_usage(self.do_info.__usage__)
            return

        agent = self.get_agent(cmd.dict)
        if not agent:
            self.error('agent not found')
            return

        if agent.agent_type != AgentManager.AGENT_TYPE_PRIMARY:
            self.error('agent not primary')
            return

        self.ack()
        body = self.server.yml(agent)
        self.print_client("%s", str(body))

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
            if not 'error' in body:
                self.ack()
        else:
            self.print_usage(self.do_sched.__usage__)
            return

        if 'error' in body:
            self.error(str(body))
        else:
            self.print_client(str(body))
        return

    @usage('firewall [ enable | disable | status ] port')
    def do_firewall(self, cmd):
        """Enable, disable or report the status of a port on an
           agent firewall.."""
        if len(cmd.args) == 1:
            if cmd.args[0] != "status":
                self.print_usage(self.do_firewall.__usage__)
                return
        elif len(cmd.args) == 2:
            if cmd.args[0] not in ("enable", "disable"):
                self.print_usage(self.do_firewall.__usage__)
                return
        else:
            self.print_usage(self.do_firewall.__usage__)
            return

        aconn = self.get_aconn(cmd.dict)
        if not aconn:
            self.error('agent not found')
            return

        if  cmd.args[0] != "status":
            try:
                port = int(cmd.args[1])
            except ValueError, e:
                self.error("firewall: Invalid port: " + cmd.args[1])
                return

        self.ack()

        if cmd.args[0] == "status":
            body = aconn.firewall.status()
        elif cmd.args[0] == "enable":
            body = aconn.firewall.enable(port)
        elif cmd.args[0] == "disable":
            body = aconn.firewall.disable(port)

        self.print_client(str(body))
        return

    @usage('ping')
    def do_ping(self, cmd):
        """Ping an agent"""
        if not len(cmd.args):
            self.print_usage(self.do_ping.__usage__)
            return

        agent = self.get_agent(cmd.dict)
        if not agent:
            self.error('agent not found')
            return

        print >> self.wfile, "Sending ping to displayname '%s' (type: %s)." % \
          (agent.displayname, agent.agent_type)

        body = self.server.ping(agent)
        self.report_status(body)

    @usage('start')
    def do_start(self, cmd):
        if len(cmd.args) != 0:
            self.print_usage(self.do_start.__usage__)
            return

        agent = self.get_agent(cmd.dict)
        if not agent:
            self.error('agent not found')
            return

        aconn = agent.connection
        # lock to ensure against two simultaneous user actions
        if not aconn.user_action_lock(blocking=False):
            self.error('busy with another user request.')
            return

        # Check to see if we're in a state to start
        stateman = self.server.stateman
        main_state = stateman.get_state()

        # Start can be done only when Tableau is stopped.
        if main_state != StateManager.STATE_STOPPED:
            self.error("Can't start - main state is: " + main_state)
            aconn.user_action_unlock()
            return

        reported_status = self.server.statusmon.get_reported_status()
        if reported_status != TableauProcess.STATUS_STOPPED:
            self.error("Can't start - reported status is: " + reported_status)
            aconn.user_action_unlock()
            return

        stateman.update(StateManager.STATE_STARTING)

        self.server.log.debug("-----------------Starting Tableau-------------------")
        # fixme: Reply with "OK" only after the agent received the command?
        self.ack()

        # Stop the maintenance web server and relinquish the web
        # server port before tabadmin start tries to listen on the web
        # server port.
        maint_body = self.server.maint("stop")
        if maint_body.has_key("error"):
            self.print_client("maint stop failed: " + str(maint_body))
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
                dict(body.items() + agent.__dict__.items()))
            stateman.update(StateManager.STATE_STOPPED)
            self.server.event_control.gen( \
                EventControl.STATE_STOPPED, agent.__dict__)
        else:
            stateman.update(StateManager.STATE_STARTED)
            self.server.event_control.gen( \
                EventControl.STATE_STARTED, agent.__dict__)

        # STARTED is set by the status monitor since it really knows the status.
        self.print_client(str(body))

        # Get the latest status from tabadmin
        self.server.statusmon.check_status_with_connection(agent)

        aconn.user_action_unlock()

    @usage('stop [no-backup|nobackup]')
    def do_stop(self, cmd):
        if len(cmd.args) > 1:
            self.error(self.do_stop.__usage__)
            return

        backup_first = True
        if len(cmd.args) == 1:
            if cmd.args[0] == "no-backup" or cmd.args[0] == "nobackup":
                backup_first = False
            else:
                self.error(self.do_stop.__usage__)

        agent = self.get_agent(cmd.dict)
        if not agent:
            self.error('agent not found')
            return

        aconn = agent.connection

        # lock to ensure against two simultaneous user actions
        if not aconn.user_action_lock(blocking=False):
            print >> self.wfile, "FAIL: Busy with another user request."
            return

        # Check to see if we're in a state to stop
        stateman = self.server.stateman
        main_state = stateman.get_state()

        # Stop can be done only if tableau is started
        if main_state != StateManager.STATE_STARTED:
            self.error("can't stop - main state is: " + main_state)
            aconn.user_action_unlock()
            return

        reported_status = self.server.statusmon.get_reported_status()
        if reported_status != TableauProcess.STATUS_RUNNING:
            print >> self.wfile, "FAIL: Can't start - reported status is:", \
                                                              reported_status
            self.server.log.debug("Can't start - reported status is: %s",  reported_status)
            aconn.user_action_unlock()
            return

        self.server.log.debug("------------Starting Backup for Stop---------------")

        stateman.update(StateManager.STATE_STARTED_BACKUP_STOP)
        self.server.event_control.gen( \
            EventControl.BACKUP_BEFORE_STOP_STARTED, agent.__dict__)
        self.ack()

        body = self.server.backup_cmd(agent)

        if not body.has_key('error'):
            self.server.event_control.gen( \
                EventControl.BACKUP_BEFORE_STOP_FINISHED,
                dict(body.items() + agent.__dict__.items()))
        else:
            self.server.event_control.gen( \
                EventControl.BACKUP_BEFORE_STOP_FAILED,
                dict(body.items() + agent.__dict__.items()))
            # FIXME: return JSON
            self.print_client("Backup failed.  Will not attempt stop.")
            aconn.user_action_unlock()
            return

        # Note: Make sure to set the state in the database before
        # we report "OK" back to the client since "OK" to the UI client
        # results in an immediate check of the state.
        stateman.update(StateManager.STATE_STOPPING)

        if not backup_first:
            # The ack was sent earlier only if a backup was attempted.
            self.ack()

        self.server.log.debug("-----------------Stopping Tableau-------------------")
        # fixme: Reply with "OK" only after the agent received the command?

        body = self.server.cli_cmd('tabadmin stop', agent)
        if not body.has_key("error"):
            # Start the maintenance server only after Tableau has stopped
            # and reqlinquished the web server port.
            maint_body = self.server.maint("start")
            if maint_body.has_key("error"):
                self.print_client("maint start failed: " + str(maint_body))

        # We set the state to stop, even though the stop failed.
        # This will be corrected by the 'tabadmin status -v' processing
        # later.
        stateman.update(StateManager.STATE_STOPPED)
        self.server.event_control.gen( \
            EventControl.STATE_STOPPED, agent.__dict__)

        # fixme: check & report status to see if it really stopped?
        self.print_client(str(body))

        # Get the latest status from tabadmin which sets the main state.
        self.server.statusmon.check_status_with_connection(agent)

        # If the 'stop' had failed, set the status to what we just
        # got back from 'tabadmin status ...'
        if body.has_key('error'):
            reported_status = self.server.statusmon.get_reported_status()
            stateman.update(reported_status)

        aconn.user_action_unlock()


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
                self.error("invalid port '%s', number required.", cmd.args[1])
                return;

        self.ack()

        body = self.server.maint(action, port)
        self.print_client(str(body))


    @usage('archive [start|stop] [port]')
    def do_archive(self, cmd):
        """Start or Stop the archive HTTPS server on the agent."""
        if len(cmd.args) < 1 or len(cmd.args) > 2:
            self.print_usage(self.do_archive.__usage__)
            return

        agent = self.get_agent(cmd.dict)
        if not agent:
            self.error('agent not found')
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
                self.error("invalid port '%s', number required.", cmd.args[1])
                return;

        self.ack()

        body = self.server.archive(agent, action, port)
        self.print_client(str(body))


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
            self.error(str(e))

        body = {}
        self.print_client(str(body))


    @usage('file [GET|PUT|DELETE] <path> [source-or-target]')
    def do_file(self, cmd):
        """Manipulate a particular file on the agent."""

        aconn = self.get_aconn(cmd.dict)
        if not aconn:
            self.error('agent not found')
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
                body = aconn.filemanager.save(path, cmd.args[2])
            elif method == 'PUT':
                if len(cmd.args) != 3:
                    self.print_usage(self.do_file.__usage__)
                    return
                self.ack()
                body = aconn.filemanager.sendfile(path, cmd.args[2])
            elif method == 'DELETE':
                if len(cmd.args) != 2:
                    self.print_usage(self.do_file.__usage__)
                    return
                self.ack()
                aconn.filemanager.delete(path)
                body = {}
            elif method == "REALPUT":
                self.ack()
                body = aconn.filemanager.put(path, cmd.args[2])
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

        self.print_client(str(body))


    @usage('s3 [GET|PUT] <bucket> <key-or-path>')
    def do_s3(self, cmd):
        """Send a file to or receive a file from an S3 bucket"""

        agent = self.get_agent(cmd.dict)
        if not agent:
            self.error('agent not found')
            return

        aconn = agent.connection
        if len(cmd.args) != 3 or len(cmd.args) > 4:
            self.print_usage(self.do_s3.__usage__)
            return

        action = cmd.args[0].upper()
        name = cmd.args[1]
        keypath = cmd.args[2]

        entry = S3.get_by_name(name)
        if not entry:
            self.error("s3 instance '" + name + "' not found.")
            return

        if 'install-dir' not in aconn.auth:
            self.error("agent connection is missing 'install-dir'")
            return
        install_dir = aconn.auth['install-dir']
        data_dir = ntpath.join(install_dir, 'data')

        self.ack()

        resource = os.path.basename(keypath)
        token = entry.get_token(resource)

        command = Controller.PS3_BIN+' %s %s "%s"' % \
            (action, entry.bucket, keypath)


        env = {u'ACCESS_KEY': token.credentials.access_key,
               u'SECRET_KEY': token.credentials.secret_key,
               u'SESSION': token.credentials.session_token,
               u'REGION_ENDPOINT': entry.region,
               u'PWD': data_dir}

        # Send command to the agent
        body = self.server.cli_cmd(command, agent, env=env)

        body[u'env'] = env
        body[u'resource'] = resource

        self.print_client(str(body))


    @usage('sql <statement>')
    def do_sql(self, cmd):
        """Run a SQL statement against the Tableau database."""

        agent = self.get_agent(cmd.dict)
        if not agent:
            self.error('agent not found')
            return

        # FIXME: check for primary agent

        if len(cmd.args) != 1:
            self.print_usage(self.do_sql.__usage__)
            return

        stmt = cmd.args[0]
        self.ack()

        body = agent.odbc.execute(stmt)
        self.print_client(str(body))


    @usage('auth [import|verify] <username> <password>')
    def do_auth(self, cmd):
        """Work with the Tableau user data."""

        if len(cmd.args) < 1:
            self.print_usage(self.do_auth.__usage__)
            return

        action = cmd.args[0].lower()

        if action == 'import':
            if len(cmd.args) != 1:
                self.print_usage(self.do_auth.__usage__)
                return
            agent = self.get_agent(cmd.dict)
            if not agent:
                self.error('agent not found')
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
        self.print_client(str(body))


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
        return self.print_client(str(body))

    @usage('ziplogs')
    def do_ziplogs(self, cmd):
        """Run 'tabadmin ziplogs'."""

        target = None
        if len(cmd.args) != 0:
            self.print_usage(self.do_backup.__usage__)
            return

        agent = self.get_agent(cmd.dict)
        if not agent:
            self.error('agent not found.')
            return

        aconn = agent.connection
        if not aconn.user_action_lock(blocking=False):
            print >> self.wfile, "FAIL: Busy with another user request."
            return

        stateman = self.server.stateman
        main_state = stateman.get_state()
        if main_state == StateManager.STATE_STARTED:
            stateman.update(StateManager.STATE_STARTED_ZIPLOGS)
        elif main_state == StateManager.STATE_STOPPED:
            stateman.update(StateManager.STATE_STOPPED_ZIPLOGS)
        else:
            print >> self.wfile, "FAIL: Main state is %s." % (main_state)
            aconn.user_action_unlock()
            return

        # FIXME: Do we want to send alerts?
        #server.event_control.gen(EventControl.BACKUP_STARTED)
        self.ack()

        body = self.server.ziplogs_cmd(agent)

        self.print_client("%s", str(body))
        if not body.has_key('error'):
            # FIXME: Do we want to send alerts?
            #server.event_control.gen(EventControl.ZIPLOGS_FINISHED, 
            #                    dict(body.items() + agent.__dict__.items()))
            pass
        else:
            # FIXME: Do we want to send alerts?
            #server.event_control.gen(EventControl.ZIPLOGS_FAILED,
            #                    dict(body.items() + agent.__dict__.items()))
            pass

        stateman.update(main_state)
        aconn.user_action_unlock();

    @usage('nop')
    def do_nop(self, cmd):
        print >> self.wfile, "dict:"
        for key in cmd.dict:
            print >> self.wfile, "\t%s = %s" % (key, cmd.dict[key])

        print >> self.wfile, "command:"
        print >> self.wfile, "\t%s" % (cmd.name)

        print >> self.wfile, "args:"
        for arg in cmd.args:
            print >> self.wfile, "\t%s" % (arg)

        self.ack()

    def get_agent(self, opts):
        agent = None

        if opts.has_key('uuid'): # should never fail
            uuid = opts['uuid'] # may be None
            if uuid:
                agent = self.server.agentmanager.agent_by_uuid(uuid)
                if not agent:
                    self.error("No connected agent with uuid=%s" % (uuid))
            else:
                self.error("No agent specified")
        else: # should never happen
            self.error("No agent specified")

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
                self.error(\
                    "CliHandler: telnet client socket failure/disconnect: " + \
                                                                        str(e))
                break

            if not data: break

            try:
                cmd = Command(self.server, data)
            except CommandException, e:
                self.error(str(e))
                continue

            if not hasattr(self, 'do_'+cmd.name):
                self.error('invalid command: %s', cmd.name)
                continue

            # <command> /displayname=X /type=primary, /uuid=Y, /hostname=Z [args]
            f = getattr(self, 'do_'+cmd.name)
            f(cmd)
