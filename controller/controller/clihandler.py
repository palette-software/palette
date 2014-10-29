import inspect
import sys
import os
import shlex
import SocketServer as socketserver
import socket
import json
import traceback

import sqlalchemy
from sqlalchemy.orm.session import make_transient

# pylint: disable=import-error,no-name-in-module
from akiri.framework.ext.sqlalchemy import meta
# pylint: enable=import-error,no-name-in-module

from agent import Agent
from agentmanager import AgentManager
from event_control import EventControl
from files import FileManager
from general import SystemConfig
from get_file import GetFile
from cloud import CloudManager, S3_ID, GCS_ID
from system import SystemEntry
from state import StateManager
from state_control import StateControl
from tableau import TableauProcess

import exc
import clierror
from util import success, failed, traceback_string, upgrade_rwlock

# pylint: disable=too-many-public-methods

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
        except ValueError, ex:
            raise CommandException(str(ex))

        doing_dict = True
        for token in tokens:
            if doing_dict:
                if token.startswith("/"):
                    token = token[1:]
                    keyvalue = token.split("=", 1)
                    if len(keyvalue) > 1:
                        key = keyvalue[0].strip()
                        value = keyvalue[1].strip()
                    else:
                        key = token.strip()
                        value = None
                    self.dict[key] = value
                else:
                    self.name = token
                    doing_dict = False
            else:
                self.args.append(token.strip())

        if not self.name:
            raise CommandException("Missing command: %s" % str(line))
        self.name = self.name.replace('-', '_')

        # This fills in any missing information in the opts dict.
        self.sanity()

    def sanity(self):
        # pylint: disable=too-many-branches
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
                query = query.filter(
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
    STATUS_OK = "OK"
    STATUS_ERROR = "error"

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
            if errnum in clierror.ERROR_STRINGS:
                msg = clierror.ERROR_STRINGS[errnum]
            else:
                msg = "No additional information"

        text = "ERROR %d %s" % (errnum, msg)
        self.print_client(text)

    def print_usage(self, msg):
        self.error(clierror.ERROR_USAGE, 'usage: '+msg)

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
        except StandardError:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            line = "ERROR %d %s.  fmt: '%s', args: '%s', Traceback: %s" % \
                (clierror.ERROR_INTERNAL,
                 sys.exc_info()[1],
                 str(fmt), str(args),
                 ''.join(traceback.format_exception(exc_type, exc_value,
                                                    exc_traceback)).\
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
        if success(body):
            body['status'] = CliHandler.STATUS_OK
        else:
            body['status'] = CliHandler.STATUS_ERROR

        self.print_client("%s", json.dumps(body))

    def do_help(self, cmd):
        # pylint: disable=unused-argument
        self.print_client('Optional prepended domain args:')
        self.print_client('    /domainid=id /domainname=name')
        self.print_client('Optional prepended agent args:')
        self.print_client('    /displayname=name /hostname=name ' + \
                                                    '/uuid=uuid /type=type')
        for name, meth in inspect.getmembers(self, predicate=inspect.ismethod):
            if name.startswith("do_"):
                name = name[3:].replace('_', '-')
                self.print_client('  ' + name)
                if meth.__doc__:
                    self.print_client('    ' + meth.__doc__)
                if hasattr(meth, '__usage__'):
                    self.print_client('    usage: ' + meth.__usage__)
        self.print_client("\n")

    @usage('status')
    def do_status(self, cmd):
        if len(cmd.args):
            self.error(clierror.ERROR_USAGE,
                       "'status' does not have an argument.")
            self.print_usage(self.do_status.__usage__)
            return

        agent = self.get_agent(cmd.dict)
        if not agent:
            # The error has already been displayed in get_agent()
            return

        self.ack()
        body = self.server.cli_cmd("tabadmin status -v", agent)
        self.report_status(body)

    @usage('test email')
    def do_test(self, cmd):
        if len(cmd.args) < 1:
            self.print_usage(self.do_test.__usage__)
            return

        action = cmd.args[0].lower()
        if action != 'email':
            self.print_usage(self.do_test.__usage__)
            return

        event_control = self.server.event_control

        event_entry = event_control.get_event_control_entry(
                      EventControl.EMAIL_TEST)

        if not event_entry:
            self.error(clierror.ERROR_INTERNAL,
                       "Missing test email event '%s'!" % \
                       EventControl.EMAIL_TEST)
            return

        self.ack()

        data = {
            "displayname": "Test email displayname",
            "info": "Test email info",
        }

        try:
            self.server.event_control.alert_email.send(event_entry, data)
        except StandardError:
            self.server.log.exception('CliHandler exception:')
            self.error(clierror.ERROR_COMMAND_FAILED, traceback_string())
            return

        self.report_status({})

    @usage('upgrade [on | off]')
    def do_upgrade(self, cmd):
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-branches

        stateman = self.server.state_manager

        if not len(cmd.args):
            upgrading = stateman.upgrading()
            if upgrading:
                msg = 'yes'
            else:
                msg = 'no'
            main_state = stateman.get_state()
            self.ack()
            self.report_status({'upgrading': msg,
                                "main-state": main_state})
            return
        if len(cmd.args) != 1:
            self.print_usage(self.do_upgrade.__usage__)
            return
        if cmd.args[0] not in ('on', 'off'):
            self.print_usage(self.do_upgrade.__usage__)
            return

        # Note: an agent doesn't have to be connected to change upgrade mode.

        if cmd.args[0] == 'on':
            self.server.log.debug(
                            "Attempting to acquire the upgrade WRITE lock.")
            self.server.upgrade_rwlock.write_acquire()
            self.server.log.debug("Acquired the upgrade WRITE lock.")

            # Check to see if we're in a state to upgrade
            main_state = stateman.get_state()

            if main_state not in (StateManager.STATE_STARTED,
                    StateManager.STATE_STOPPED,
                    StateManager.STATE_STOPPED_UNEXPECTED,
                    StateManager.STATE_DEGRADED,
                    StateManager.STATE_PENDING,
                    StateManager.STATE_DISCONNECTED):

                msg = "Can't upgrade - main state is: " + main_state
                self.error(clierror.ERROR_BUSY, 'FAIL: ' + msg)
                self.server.log.debug(msg)

                self.server.upgrade_rwlock.write_release()

                return

            self.server.system.save(SystemConfig.UPGRADING, 'yes')

            self.ack()
            self.report_status({})
            return

        # Disable upgrade
        self.server.system.save(SystemConfig.UPGRADING, 'no')
        main_state = stateman.get_state()

        try:
            self.server.upgrade_rwlock.write_release()
        except RuntimeError, ex:
            self.error(clierror.ERROR_COMMAND_FAILED,
                       "FAIL: Can't disable upgrade: " + \
                       "upgrading: %s, " + \
                       "main state: %s, " + \
                       "error: %s",
                       stateman.upgrading(),
                       main_state,
                       str(ex))
            self.server.log.debug(
                       "FAIL: Can't disable upgrade: " + \
                       "upgrading: %s, " + \
                       "main state: %s, " + \
                       "error: %s",
                       stateman.upgrading(),
                       main_state,
                       str(ex))
            return

        self.ack()
        self.report_status({})

    @usage('backup')
    @upgrade_rwlock
    def do_backup(self, cmd):
        """Perform a Tableau backup and potentially migrate."""
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        # pylint: disable=invalid-name

        if len(cmd.args):
            self.print_usage(self.do_backup.__usage__)
            return

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        aconn = agent.connection

        # lock to ensure against two simultaneous user actions
        if not aconn.user_action_lock(blocking=False):
            self.error(clierror.ERROR_BUSY)
            return

        # Check to see if we're in a state to backup
        stateman = self.server.state_manager
        main_state = stateman.get_state()

        # Backups can be done when Tableau is started, degraded or stopped.
        if main_state not in (StateManager.STATE_STARTED,
                    StateManager.STATE_DEGRADED, StateManager.STATE_STOPPED,
                    StateManager.STATE_STOPPED_UNEXPECTED):
            self.error(clierror.ERROR_BUSY,
                       "FAIL: Can't backup - main state is: %s", main_state)
            self.server.log.debug("Can't backup - main state is: " + main_state)
            aconn.user_action_unlock()
            return

        reported_status = self.server.statusmon.get_reported_status()
        # The reported status from Tableau needs to be running or stopped
        # to do a backup.
        if reported_status in (TableauProcess.STATUS_RUNNING,
                                        TableauProcess.STATUS_DEGRADED):
            stateman.update(StateManager.STATE_STARTED_BACKUP)
        elif reported_status == TableauProcess.STATUS_STOPPED:
            stateman.update(StateManager.STATE_STOPPED_BACKUP)
        else:
            msg = "Can't backup - reported status is: " + reported_status
            self.error(clierror.ERROR_WRONG_STATE, 'FAIL: ' + msg)
            self.server.log.debug(msg)
            aconn.user_action_unlock()
            return

        self.server.log.debug("---------------Starting Backup-----------------")
        if cmd.dict.has_key('userid'):
            userid = int(cmd.dict['userid'])
        else:
            userid = None

        if userid != None:
            backup_started_event = EventControl.BACKUP_STARTED
            backup_finished_event = EventControl.BACKUP_FINISHED
            backup_finished_copy_failed_event = \
                                    EventControl.BACKUP_FINISHED_COPY_FAILED
            backup_failed_event = EventControl.BACKUP_FAILED
        else:
            backup_started_event = EventControl.BACKUP_STARTED_SCHEDULED
            backup_finished_event = EventControl.BACKUP_FINISHED_SCHEDULED
            backup_finished_copy_failed_event = \
                            EventControl.BACKUP_FINISHED_SCHEDULED_COPY_FAILED
            backup_failed_event = EventControl.BACKUP_FAILED_SCHEDULED

        data = agent.todict()
        self.server.event_control.gen(backup_started_event, data, userid=userid)
        self.ack()

        try:
            body = self.server.backup_cmd(agent, userid)
        except StandardError:
            self.server.log.exception("Backup Exception:")
            line = "Backup Error. Traceback: %s" % traceback_string()
            body = {'error': line, 'info': 'Failure'}

        # delete/rotate old backups
        rotate_info = self.server.rotate_backups()
        body['info'] += rotate_info

        data = agent.todict()
        if success(body):
            if 'copy-failed' in body:
                real_event = backup_finished_copy_failed_event
            else:
                real_event = backup_finished_event
            self.server.event_control.gen(real_event,
                                          dict(body.items() + data.items()),
                                          userid=userid)
        else:
            self.server.event_control.gen(backup_failed_event,
                                          dict(body.items() + data.items()),
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


    @usage('deletefile file-name')
    @upgrade_rwlock
    def do_deletefile(self, cmd):
        """Delete a file in the 'files' table."""

        if len(cmd.args) != 1:
            self.print_usage(self.do_deletefile.__usage__)
            return
        filename = cmd.args[0]

        entry = self.server.files.find_by_name(filename)
        if not entry:
            self.error(clierror.ERROR_NOT_FOUND, "File not found: %s", filename)
            return

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        aconn = agent.connection

        if not aconn:
            self.error(clierror.ERROR_AGENT_NOT_FOUND)
            return

        if not aconn.user_action_lock(blocking=False):
            self.error(clierror.ERROR_BUSY)
            return

        stateman = self.server.state_manager
        main_state = stateman.get_state()
        if main_state in (StateManager.STATE_STARTED,
                                                StateManager.STATE_DEGRADED):
            stateman.update(StateManager.STATE_STARTED_FILEDEL)
        elif main_state in (StateManager.STATE_STOPPED,
                            StateManager.STATE_STOPPED_UNEXPECTED):
            stateman.update(StateManager.STATE_STOPPED_FILEDEL)
        else:
            self.error(clierror.ERROR_WRONG_STATE,
                       "FAIL: Main state is %s." % (main_state))
            aconn.user_action_unlock()
            return

        self.ack()
        body = self.server.delfile_cmd(entry)

        stateman.update(main_state)

        aconn.user_action_unlock()
        self.report_status(body)

    @usage('http_request IMPORT')
    @upgrade_rwlock
    def do_http_request(self, cmd):
        """Import http_requests table from Tableau"""

        # Reserved for later expansion
        if len(cmd.args) != 1 or cmd.args[0].upper() != 'IMPORT':
            self.print_usage(self.do_http_request.__usage__)
            return

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        if not self.server.odbc_ok():
            state = self.server.state_manager.get_state()
            self.error(clierror.ERROR_WRONG_STATE,
                       "FAIL: Main state is %s." % state)
            return

        self.ack()
        body = self.server.hrman.load(agent)
        self.report_status(body)


    @usage('workbook [IMPORT|FIXUP]')
    @upgrade_rwlock
    def do_workbook(self, cmd):
        """Import workbooks table from Tableau or fixup a previous import"""

        if len(cmd.args) != 1:
            self.print_usage(self.do_workbook.__usage__)
            return

        action = cmd.args[0].lower()
        if action != 'import' and action != 'fixup':
            self.print_usage(self.do_workbook.__usage__)
            return

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        if not self.server.odbc_ok():
            state = self.server.state_manager.get_state()
            self.error(clierror.ERROR_WRONG_STATE,
                       "FAIL: Main state is " + state)
            return

        self.ack()
        if action == 'import':
            body = self.server.workbooks.load(agent)
        elif action == 'fixup':
            body = self.server.workbooks.fixup(agent)
        self.report_status(body)


    @usage('extract IMPORT')
    @upgrade_rwlock
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
            state = self.server.state_manager.get_state()
            self.error(clierror.ERROR_WRONG_STATE,
                       "FAIL: Main state is " + state)
            return

        self.ack()
        body = self.server.extract.load(agent)
        self.report_status(body)


    @usage('[/no-config] restore backup-name')
    @upgrade_rwlock
    def do_restore(self, cmd):
        """Restore.
        The "name" is not a full path-name, but is the backup
        filename from the 'backup' table.
        """
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements

        if len(cmd.args) != 1:
            self.print_usage(self.do_restore.__usage__)
            return

        backup_name = cmd.args[0]

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        aconn = agent.connection

        if cmd.dict.has_key('userid'):
            userid = int(cmd.dict['userid'])
        else:
            userid = None

        # lock to ensure against two simultaneous user actions
        if not aconn.user_action_lock(blocking=False):
            self.error(clierror.ERROR_BUSY)
            return

        # Check to see if we're in a state to restore
        stateman = self.server.state_manager
        main_state = stateman.get_state()

        # Backups can be done when Tableau is either started, degraded
        # or stopped.
        if main_state not in (StateManager.STATE_STARTED,
                    StateManager.STATE_DEGRADED, StateManager.STATE_STOPPED,
                    StateManager.STATE_STOPPED_UNEXPECTED):
            msg = "Can't backup before restore - main state is: " + main_state
            self.error(clierror.ERROR_WRONG_STATE, "FAIL: " + msg)
            self.server.log.debug(msg)
            aconn.user_action_unlock()
            return

        data = agent.todict()

        if cmd.dict.has_key('no-config'):
            no_config = True
            data['restore_type'] = 'Data only'
        else:
            no_config = False
            data['restore_type'] = 'Data and Configuration'

        # Do a quick check to make sure the file to restore from
        # is available.  In particular, if the file is on an agent,
        # make sure the agent is enabled.
        try:
            GetFile(self.server, agent, backup_name, check_only=True)
        except IOError as ex:
            self.error(clierror.ERROR_COMMAND_FAILED, str(ex))
            self.server.log.debug(str(ex))
            body = {'stderr': ex, 'stdout':"", "error":""}
            self.server.event_control.gen(EventControl.RESTORE_FAILED,
                                          dict(body.items() + data.items()),
                                          userid=userid)

            aconn.user_action_unlock()
            return

        reported_status = self.server.statusmon.get_reported_status()
        # The reported status from Tableau needs to be running or stopped
        # to do a backup.  If it is, set our state to
        # STATE_*_BACKUP_RESTORE.
        if reported_status in (TableauProcess.STATUS_RUNNING,
                               TableauProcess.STATUS_DEGRADED):
            stateman.update(StateManager.STATE_STARTED_BACKUP_RESTORE)
        elif reported_status == TableauProcess.STATUS_STOPPED:
            stateman.update(StateManager.STATE_STOPPED_BACKUP_RESTORE)
        else:
            msg = "Can't backup before restore - status is: " + reported_status
            self.error(clierror.ERROR_WRONG_STATE, "FAIL: " + msg)
            self.server.log.debug(msg)
            aconn.user_action_unlock()
            return

        # Do a backup before we try to do a restore.
        #FIXME: refactor do_backup() into do_backup() and backup()
        self.server.log.debug("----------Starting Backup for Restore----------")
        self.server.event_control.gen(
            EventControl.BACKUP_BEFORE_RESTORE_STARTED, data, userid=userid)

        self.ack()

        # Before we do anything, do a license check, which automatically
        # sends an event if appropriate.
        license_body = self.server.license_manager.check(agent)
        if failed(license_body):
            stateman.update(main_state)
            self.report_status(license_body)
            aconn.user_action_unlock()
            return

        # No alerts or state updates are done in backup_cmd().
        try:
            body = self.server.backup_cmd(agent, userid)
        except StandardError:
            self.server.log.exception("Backup for Restore Exception:")
            line = "Backup For Restore Error. Traceback: %s" % \
                    traceback_string()
            body = {'error': line}

        if success(body):
            if 'copy-failed' in body:
                real_event = \
                       EventControl.BACKUP_BEFORE_RESTORE_FINISHED_COPY_FAILED
            else:
                real_event = EventControl.BACKUP_BEFORE_RESTORE_FINISHED
            self.server.event_control.gen(real_event,
                dict(body.items() + data.items()),
                userid=userid)
        else:
            self.server.event_control.gen(
                EventControl.BACKUP_BEFORE_RESTORE_FAILED,
                dict(body.items() + data.items()),
                userid=userid)

            self.report_status(body)
            stateman.update(main_state)
            aconn.user_action_unlock()
            return

        self.server.log.debug("-------------Starting Restore---------------")

        # restore_cmd() updates the state correctly depending on the
        # success of backup, copy, stop, restore, etc.
        try:
            body = self.server.restore_cmd(agent, backup_name, main_state,
                                            no_config=no_config, userid=userid)
        except StandardError:
            self.server.log.exception("Restore Exception:")
            line = "Restore Error: Traceback: %s" % traceback_string()
            body = {'error': line}

        # The final RESTORE_FINISHED/RESTORE_FAILED alert is sent only here and
        # not in restore_cmd().  Intermediate alerts like RESTORE_STARTED
        # are sent in restore_cmd().
        if success(body):
            # Delete/rotate old backups AFTER the restore succeeded.
            #
            # If the restore failed, we could end up with more than
            # the configured number of backups saved, due to the
            # auto-backup-before-restore adding one.  But, it is
            # better to have too many backups than deleting
            # a backup that could be needed while the user is wanting
            # to do a restore.

            rotate_info = self.server.rotate_backups()
            if 'stdout' in body:
                body['stdout'] += rotate_info
            else:
                body['stdout'] = rotate_info

            # Restore finished successfully.  The main state has.
            # already been set.
            self.server.event_control.gen(EventControl.RESTORE_FINISHED,
                                          dict(body.items() + data.items()),
                                          userid=userid)
        else:
            self.server.event_control.gen(EventControl.RESTORE_FAILED,
                                          dict(body.items() + data.items()),
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

        self.ack()
        body = self.server.copy_cmd(cmd.args[0], cmd.args[1], cmd.args[2])
        self.report_status(body)

    # FIXME: print status too
    def list_agents(self):
        agents = self.server.agentmanager.all_agents()
        if len(agents) == 0:
            self.report_status({'agents':[]})
            return

        # FIXME: print the agent state too.
        agent_dict_list = []
        for key in agents:
            data = agents[key].todict(pretty=True)
            agent_dict_list.append(data)
        self.report_status({'agents': agent_dict_list})

    def list_files(self):
        # FIXME: per environment
        files = []
        for fileent in FileManager.all(self.server.domain.domainid):
            files.append(fileent.todict(pretty=True))
        self.report_status({'files': files})

    @usage('list [agents|files]')
    def do_list(self, cmd):
        """List information about all connected agents."""

        f = None
        if len(cmd.args) == 0:
            f = self.list_agents
        elif len(cmd.args) == 1:
            if cmd.args[0].lower() == 'agents':
                f = self.list_agents
            elif cmd.args[0].lower() == 'files':
                f = self.list_files
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


    @usage('tabcmd [args...]')
    def do_tabcmd(self, cmd):

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        self.ack()

        if cmd.args:
            args = cmd.args[0]
            for arg in cmd.args[1:]:
                if ' ' in arg:
                    args += ' "' + arg + '" '
                else:
                    args += ' ' + arg
        else:
            args = ''
        body = self.server.tabcmd(args, agent)
        self.report_status(body)

    @usage('phttp GET|PUT <URL> [source-or-destination]')
    def do_phttp(self, cmd):
        if len(cmd.args) < 2:
            self.print_usage(self.do_phttp.__usage__)
            return

        agent = self.get_agent(cmd.dict)
        if not agent:
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
    @upgrade_rwlock
    def do_info(self, cmd):
        # pylint: disable=too-many-return-statements
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
                return

            self.ack()
            try:
                body = self.server.get_pinfo(agent, update_agent=True)
            except IOError as ex:
                self.error(clierror.ERROR_COMMAND_FAILED, str(ex))
                self.server.log.info("pinfo failed: %s", str(ex))
                return

            self.report_status(body)
            return

        self.ack()

        agents = self.server.agentmanager.all_agents()
        if len(agents) == 0:
            self.report_status({})
            return

        pinfos = []
        for key in agents.keys():
            try:
                agent = agents[key]
            except StandardError:
                # This agent is now gone
                continue

            try:
                body = self.server.get_pinfo(agent, update_agent=True)
            except IOError as ex:
                self.error(clierror.ERROR_COMMAND_FAILED, str(ex))
                self.server.log.info("pinfo failed for agent '%s': %s",
                                            agent.displayname, str(ex))
                return

            pinfos.append(body)

        self.report_status({"info": pinfos})

    @usage('license [repair]')
    @upgrade_rwlock
    def do_license(self, cmd):
        """Run license check."""
        repair = False
        if len(cmd.args) > 1:
            self.print_usage(self.do_license.__usage__)
            return
        if len(cmd.args) == 1:
            action = cmd.args[0].lower()
            if action == 'repair':
                repair = True
            elif action != 'check':
                self.print_usage(self.do_license.__usage__)
                return

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        if not self.server.odbc_ok():
            state = self.server.state_manager.get_state()
            self.error(clierror.ERROR_WRONG_STATE,
                       "FAIL: Main state is " + state)
            return

        self.ack()
        if repair:
            body = self.server.license_manager.repair(agent)
        else:
            body = self.server.license_manager.check(agent)
        self.report_status(body)

    @usage('yml')
    @upgrade_rwlock
    def do_yml(self, cmd):
        if len(cmd.args):
            self.print_usage(self.do_yml.__usage__)
            return

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        if agent.agent_type != AgentManager.AGENT_TYPE_PRIMARY:
            self.error(clierror.ERROR_AGENT_NOT_PRIMARY)
            return

        self.ack()
        try:
            body = self.server.yml_sync(agent)
        except IOError as ex:
            self.error(clierror.ERROR_COMMAND_FAILED,
                       "FAIL: Can't get yml: %s", str(ex))
            self.server.log.debug("FAIL: Can't get yml: %s", str(ex))
            return
        self.report_status(body)

    @usage('sched [status | delete job-name [job-name ...] | ' + \
               'add min hour dom mon dow command ]\n' + \
               'Note: dow uses 0 for Monday while cron dow uses 0 for Sunday')
    @upgrade_rwlock
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
            name = args[5]
            body = self.server.sched.add_cron_job(name, minute=args[0],
                                                  hour=args[1],
                                                  day_of_month=args[2],
                                                  month=args[3],
                                                  day_of_week=args[4])
            if success(body):
                self.ack()
        else:
            self.print_usage(self.do_sched.__usage__)
            return

        if failed(body):
            self.error(clierror.ERROR_COMMAND_FAILED, str(body))
        else:
            self.report_status(body)
        return

    @usage('checkports')
    @upgrade_rwlock
    def do_checkports(self, cmd):
        """Check on all outgoing port connections."""

        if len(cmd.args):
            self.print_usage(self.do_checkports.__usage__)
            return

        stateman = self.server.state_manager
        main_state = stateman.get_state()
        if main_state in (StateManager.STATE_PENDING,
                          StateManager.STATE_DISCONNECTED):
            self.error(clierror.ERROR_WRONG_STATE, main_state)
            return

        if not self.server.ports.check_ports_lock(blocking=False):
            self.error(clierror.ERROR_BUSY, \
                "Port check is already running on behalf of another request")
            return

        self.ack()

        body = self.server.ports.check_ports()
        self.server.ports.check_ports_unlock()

        self.report_status(body)


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
            except ValueError, ex:
                self.error(clierror.ERROR_INVALID_PORT,
                           "firewall: Invalid port: " + str(ex))
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
    @upgrade_rwlock
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
            self.error(clierror.ERROR_BUSY)
            return

        # Check to see if we're in a state to start
        stateman = self.server.state_manager
        main_state = stateman.get_state()

        # Start can be done only when Tableau is stopped.
        if main_state not in (StateManager.STATE_STOPPED,
                              StateManager.STATE_STOPPED_UNEXPECTED):
            self.error(clierror.ERROR_WRONG_STATE,
                       "Can't start - main state is: " + main_state)
            aconn.user_action_unlock()
            return

        reported_status = self.server.statusmon.get_reported_status()
        if reported_status != TableauProcess.STATUS_STOPPED:
            self.error(clierror.ERROR_WRONG_STATE,
                       "Can't start - reported status is: " + reported_status)
            aconn.user_action_unlock()
            return

        stateman.update(StateManager.STATE_STARTING)

        self.server.log.debug("--------------Starting Tableau----------------")
        # fixme: Reply with "OK" only after the agent received the command?
        self.ack()

        if cmd.dict.has_key('userid'):
            userid = int(cmd.dict['userid'])
        else:
            userid = None

        # Stop the maintenance web server and relinquish the web
        # server port before tabadmin start tries to listen on the web
        # server port.

        self.server.maint("stop")
        # FIXME: let it continue ?

        body = self.server.cli_cmd('tabadmin start', agent)
        if body.has_key("exit-status"):
            exit_status = body['exit-status']
        else:
            exit_status = 1 # if no 'exit-status' then consider it failed.

        data = agent.todict()
        if exit_status:
            # The "tableau start" failed.  Go back to "STOPPED" state.
            self.server.event_control.gen(EventControl.TABLEAU_START_FAILED,
                                          dict(body.items() + data.items()),
                                          userid=userid)
            stateman.update(StateManager.STATE_STOPPED)
            self.server.event_control.gen(EventControl.STATE_STOPPED,
                                          data, userid=userid)
        else:
            stateman.update(StateManager.STATE_STARTED)
            self.server.event_control.gen(EventControl.STATE_STARTED,
                                          data, userid=userid)

        # Get the latest status from tabadmin
        self.server.statusmon.check_status_with_connection(agent)

        aconn.user_action_unlock()
        # STARTED is set by the status monitor since it really knows the status.
        self.report_status(body)

    def pre_stop(self, action, agent, userid, license_check, backup_first):
        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        """Do license check and backup as specified in the command line
           arguments.  This is used by do_stop() and do_restart().
           Must be called with the user_action_lock().
           Will unlock it on failure.

           Returns:
                True on success
                Fail on failure with the user_action_lock unlocked.
        """

        aconn = agent.connection

        # Stop can be done only if Tableau is started
        good_states = [StateManager.STATE_STARTED, StateManager.STATE_DEGRADED]
        good_reported_status = [TableauProcess.STATUS_RUNNING,
                                TableauProcess.STATUS_DEGRADED]
        if action == StateControl.ACTION_RESTART:
            # Restart can also be done when Tableau is stopped.
            good_states += [StateManager.STATE_STOPPED,
                            StateManager.STATE_STOPPED_UNEXPECTED]

            good_reported_status.append(TableauProcess.STATUS_STOPPED)

        # Check to see if we're in a state to stop or restart
        stateman = self.server.state_manager
        main_state = stateman.get_state()

        if main_state not in good_states:
            self.error(clierror.ERROR_WRONG_STATE,
                       "can't stop - main state is: " + main_state)
            aconn.user_action_unlock()
            return False

        reported_status = self.server.statusmon.get_reported_status()
        if reported_status not in good_reported_status:
            msg = "Can't stop/restart - reported status is: " + reported_status
            self.error(clierror.ERROR_WRONG_STATE, "FAIL: " + msg)
            self.server.log.debug(msg)
            aconn.user_action_unlock()
            return False

        self.ack()
        # Before we do anything, do a license check, which automatically
        # sends an event if appropriate.
        if license_check:
            license_body = self.server.license_manager.check(agent)
            if failed(license_body):
                stateman.update(main_state)
                self.report_status(license_body)
                aconn.user_action_unlock()
                return False

        if action == StateControl.ACTION_STOP:
            state_started = StateManager.STATE_STARTED_BACKUP_STOP

            event_started = EventControl.BACKUP_BEFORE_STOP_STARTED
            event_finished = EventControl.BACKUP_BEFORE_STOP_FINISHED
            event_copy_failed = \
                        EventControl.BACKUP_BEFORE_STOP_FINISHED_COPY_FAILED
            event_backup_failed = EventControl.BACKUP_BEFORE_STOP_FAILED
        else:
            state_started = StateManager.STATE_STARTED_BACKUP_RESTART

            event_started = EventControl.BACKUP_BEFORE_RESTART_STARTED
            event_finished = EventControl.BACKUP_BEFORE_RESTART_FINISHED
            event_copy_failed = \
                        EventControl.BACKUP_BEFORE_RESTART_FINISHED_COPY_FAILED
            event_backup_failed = EventControl.BACKUP_BEFORE_RESTART_FAILED

        if backup_first:
            self.server.log.debug(
                "------------Starting Backup before %s---------------" % action)
            stateman.update(state_started)

            data = agent.todict()
            self.server.event_control.gen(event_started, data, userid=userid)

            body = self.server.backup_cmd(agent, userid)

            if success(body):
                if 'copy-failed' in body:
                    real_event = event_copy_failed
                else:
                    real_event = event_finished
                self.server.event_control.gen(real_event,
                    dict(body.items() + data.items()),
                    userid=userid)
            else:
                self.server.event_control.gen(event_backup_failed,
                    dict(body.items() + data.items()),
                    userid=userid)

                # Backup failed.  Will not attempt stop
                msg = 'Backup failed.  Will not attempt stop'
                if 'info' in body:
                    body['info'] += '\n' + msg
                else:
                    body['info'] = msg
                self.report_status(body)
                aconn.user_action_unlock()
                return False

        return True

    @usage('restart [no-backup|nobackup] [no-license|nolicense]')
    @upgrade_rwlock
    def do_restart(self, cmd):
        backup_first = True
        license_check = True

        for arg in cmd.args:
            arg = arg.lower()
            if arg == "no-backup" or arg == "nobackup":
                backup_first = False
            elif arg == "no-license" or arg == "nolicense":
                license_check = False
            else:
                self.print_usage(self.do_restart.__usage__)
                return

        if cmd.dict.has_key('userid'):
            userid = int(cmd.dict['userid'])
        else:
            userid = None

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        aconn = agent.connection

        # lock to ensure against two simultaneous user actions
        if not aconn.user_action_lock(blocking=False):
            self.error(clierror.ERROR_BUSY)
            return

        # Do the license check and backup, if appropriate
        if not self.pre_stop(StateControl.ACTION_RESTART, agent, userid,
                             license_check, backup_first):
            return

        stateman = self.server.state_manager
        # Note: Make sure to set the state in the database before
        # we report "OK" back to the client since "OK" to the UI client
        # results in an immediate check of the state.
        stateman.update(StateManager.STATE_RESTARTING)

        self.server.log.debug("-------------Restarting Tableau----------------")
        # fixme: Reply with "OK" only after the agent received the command?
        body = self.server.cli_cmd('tabadmin restart', agent)

        data = agent.todict()

        if failed(body):
            # We set the state to stopped, even though the stop failed.
            # This will be corrected by the 'tabadmin status -v' processing
            # later.
            stateman.update(StateManager.STATE_STOPPED)
            self.server.event_control.gen(EventControl.RESTART_FAILED,
                                          dict(body.items() + data.items()),
                                          userid=userid)
        else:
            stateman.update(StateManager.STATE_STARTED)
            self.server.event_control.gen(EventControl.RESTART_FINISHED,
                                          dict(body.items() + data.items()),
                                          userid=userid)

        # Get the latest status from tabadmin which sets the main state.
        self.server.statusmon.check_status_with_connection(agent)

        aconn.user_action_unlock()

        # fixme: check & report status to see if it really stopped?
        self.report_status(body)

    @usage('stop [no-backup|nobackup] [no-license|nolicense]' +\
           ' [no-maint|nomaint]')
    @upgrade_rwlock
    def do_stop(self, cmd):
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        backup_first = True
        license_check = True
        start_maint = True

        for arg in cmd.args:
            arg = arg.lower()
            if arg == "no-backup" or arg == "nobackup":
                backup_first = False
            elif arg == "no-license" or arg == "nolicense":
                license_check = False
            elif arg == "no-maint" or arg == "nomaint":
                start_maint = False
            else:
                self.print_usage(self.do_stop.__usage__)
                return

        if cmd.dict.has_key('userid'):
            userid = int(cmd.dict['userid'])
        else:
            userid = None

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        aconn = agent.connection

        # lock to ensure against two simultaneous user actions
        if not aconn.user_action_lock(blocking=False):
            self.error(clierror.ERROR_BUSY)
            return

        # Do the license check and backup, if appropriate
        if not self.pre_stop(StateControl.ACTION_STOP, agent, userid,
                             license_check, backup_first):
            return

        stateman = self.server.state_manager
        # Note: Make sure to set the state in the database before
        # we report "OK" back to the client since "OK" to the UI client
        # results in an immediate check of the state.
        stateman.update(StateManager.STATE_STOPPING)

        self.server.log.debug("--------------Stopping Tableau-----------------")
        # fixme: Reply with "OK" only after the agent received the command?
        body = self.server.cli_cmd('tabadmin stop', agent)
        if success(body) and start_maint:
            # Start the maintenance server only after Tableau has stopped
            # and reqlinquished the web server port.
            maint_body = self.server.maint("start")
            if failed(maint_body):
                msg = "maint start failed: " + str(maint_body)
                if not 'info' in body:
                    body['info'] = msg
                else:
                    body['info'] += "\n" + msg

        # We set the state to stop, even though the stop failed.
        # This will be corrected by the 'tabadmin status -v' processing
        # later.
        stateman.update(StateManager.STATE_STOPPED)
        self.server.event_control.gen(EventControl.STATE_STOPPED,
                                      agent.todict(), userid=userid)

        # Get the latest status from tabadmin which sets the main state.
        self.server.statusmon.check_status_with_connection(agent)

        # If the 'stop' had failed, set the status to what we just
        # got back from 'tabadmin status ...'
        if failed(body):
            reported_status = self.server.statusmon.get_reported_status()
            stateman.update(reported_status)

        aconn.user_action_unlock()

        # fixme: check & report status to see if it really stopped?
        self.report_status(body)

    @usage('maint start|stop')
    def do_maint(self, cmd):
        """Start or Stop the maintenance webserver on the agent."""

        if len(cmd.args) != 1:
            self.print_usage(self.do_maint.__usage__)
            return

        action = cmd.args[0].lower()
        if action != "start" and action != "stop":
            self.print_usage(self.do_maint.__usage__)
            return

        self.ack()

        body = self.server.maint(action)
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
            except ValueError:
                self.error(clierror.ERROR_INVALID_PORT,
                           "invalid port '%s', number required.", cmd.args[1])
                return

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
        except ValueError, ex:
            self.error(clierror.ERROR_COMMAND_FAILED, str(ex))

        body = {}
        self.report_status(body)


    @usage('file [GET|PUT|DELETE|SHA256|MOVE|LISTDIR|SIZE|MKDIRS|WRITE]' +\
           ' <path> [arg]')
    def do_file(self, cmd):
        """Manipulate a particular file on the agent."""
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements

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
        except exc.HTTPException, ex:
            body = {'error': 'HTTP Failure',
                 'status-code': ex.status,
                 'reason-phrase': ex.reason,
                 }
            if ex.method:
                body['method'] = ex.method
            if ex.body:
                body['body'] = ex.body
        except IOError, ex:
            body = {'error': str(ex)}

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

    def _do_cloud(self, cloud_type, usage_msg, cmd):
        # pylint: disable=too-many-branches

        if cloud_type == CloudManager.CLOUD_TYPE_S3:
            cloud_type_id = S3_ID
            cloud_instance = self.server.cloud.s3
        elif cloud_type == CloudManager.CLOUD_TYPE_GCS:
            cloud_type_id = GCS_ID
            cloud_instance = self.server.cloud.gcs
        else:
            raise ValueError('cloud_type')

        if len(cmd.args) == 2:
            dirpath = None
        elif len(cmd.args) == 3:
            dirpath = cmd.args[2]
        else:
            self.print_usage(usage_msg)
            return

        action = cmd.args[0].upper()
        if action not in ('GET', 'PUT', 'DELETE'):
            self.error(clierror.ERROR_COMMAND_SYNTAX_ERROR,
                       "Invalid action: %s", action)
            return

        if action != 'DELETE':
            agent = self.get_agent(cmd.dict)
            if not agent:
                return

        keypath = cmd.args[1]

        # FIXME: move to CloudManager ?
        if 'name' in cmd.dict:
            name = cmd.dict['name']
            entry = self.server.cloud.get_by_name(name, cloud_type)
            if not entry:
                self.error(clierror.ERROR_NOT_FOUND,
                           "cloud instance '" + name + "' not found.")
                return
        else:
            # FIXME: duplicate code with webapp.
            cloudid = self.server.system.getint(cloud_type_id, default=0)
            if cloudid == 0:
                self.error(clierror.ERROR_NOT_FOUND,
                           'No default cloud instance specified.')
                return
            entry = self.server.cloud.get_by_cloudid(cloudid)
            if not entry:
                self.error(clierror.ERROR_NOT_FOUND,
                           "cloud instance '" + str(cloudid) + "' not found.")
                return

        self.ack()

        if action == 'GET':
            body = cloud_instance.get(agent, entry, keypath, pwd=dirpath)
        elif action == 'PUT':
            body = cloud_instance.put(agent, entry, keypath, pwd=dirpath)
        elif action == 'DELETE':
            body = cloud_instance.delete_file(entry, keypath)

        self.report_status(body)

    # 's3-name' is now a slash ('/') parameter
    @usage('s3 [GET|PUT|DELETE] <key-or-path> [dirpath]')
    def do_s3(self, cmd):
        """Send a file to or receive a file from an S3 bucket"""
        return self._do_cloud(CloudManager.CLOUD_TYPE_S3,
                              self.do_s3.__usage__,
                              cmd)

    # 'gcs-name' is now a slash ('/') parameter
    @usage('gcs [GET|PUT|DELETE] <key-or-path> [dirpath]')
    def do_gcs(self, cmd):
        """Send a file to or receive a file from a GCP bucket"""
        return self._do_cloud(CloudManager.CLOUD_TYPE_GCS,
                              self.do_gcs.__usage__,
                              cmd)

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
            state = self.server.state_manager.get_state()
            self.error(clierror.ERROR_WRONG_STATE,
                       "FAIL: Main state is " + state)
            return

        stmt = cmd.args[0]
        self.ack()

        body = agent.odbc.execute(stmt)
        self.report_status(body)

    @usage('auth [import|verify] <username> <password>')
    @upgrade_rwlock
    def do_auth(self, cmd):
        """Work with the Tableau user data."""

        if len(cmd.args) < 1:
            self.print_usage(self.do_auth.__usage__)
            return

        action = cmd.args[0].lower()

        if not self.server.odbc_ok():
            state = self.server.state_manager.get_state()
            self.error(clierror.ERROR_WRONG_STATE,
                       "FAIL: Main state is " + state)
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
            windomain = self.server.yml.get("wgserver.domain.fqdn",
                                            default=None)
            if not windomain:
                self.error(clierror.ERROR_WRONG_STATE,
                           "FAIL: No ActiveDirectory domain specified.")
                return
            self.ack()
            body = self.server.active_directory_verify(agent,
                                                       windomain,
                                                       cmd.args[1],
                                                       cmd.args[2])
        else:
            self.print_usage(self.do_ad.__usage__)
            return
        self.report_status(body)

    @usage('sync')
    @upgrade_rwlock
    def do_sync(self, cmd):
        """Synchronize Tableau tables."""

        if len(cmd.args) != 0:
            self.print_usage(self.do_sync.__usage__)
            return

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        if not self.server.odbc_ok():
            state = self.server.state_manager.get_state()
            self.error(clierror.ERROR_WRONG_STATE,
                       "FAIL: Main state is " + state)
            return

        self.ack()
        body = self.server.sync_cmd(agent)

        if failed(body):
            self.error(clierror.ERROR_COMMAND_FAILED, str(body))
        else:
            self.print_client("%s", json.dumps(body))

    @usage('system <SET|GET|DELETE> <key> [value]')
    def do_system(self, cmd):
        """ Set or Delete a 'system' table entry for the current environment."""
        # pylint: disable=too-many-branches
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
    @upgrade_rwlock
    def do_ziplogs(self, cmd):
        """Run 'tabadmin ziplogs'."""

        if len(cmd.args) != 0:
            self.print_usage(self.do_ziplogs.__usage__)
            return

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        aconn = agent.connection
        if not aconn.user_action_lock(blocking=False):
            self.error(clierror.ERROR_WRONG_STATE)
            return

        stateman = self.server.state_manager
        main_state = stateman.get_state()
        if main_state in (StateManager.STATE_STARTED,
                                                StateManager.STATE_DEGRADED):
            stateman.update(StateManager.STATE_STARTED_ZIPLOGS)
        elif main_state in (StateManager.STATE_STOPPED,
                            StateManager.STATE_STOPPED_UNEXPECTED):
            stateman.update(StateManager.STATE_STOPPED_ZIPLOGS)
        else:
            self.error(clierror.ERROR_WRONG_STATE,
                       "FAIL: Main state is " + main_state)
            aconn.user_action_unlock()
            return

        if cmd.dict.has_key('userid'):
            userid = int(cmd.dict['userid'])
        else:
            userid = None

        self.ack()

        body = self.server.ziplogs_cmd(agent, userid=userid)
        if failed(body):
            data = agent.todict()
            self.server.event_control.gen(EventControl.ZIPLOGS_FAILED,
                                          dict(body.items() + data.items()),
                                          userid=userid)

        stateman.update(main_state)
        aconn.user_action_unlock()

        self.report_status(body)
        # Events are generated in ziplogs_cmd

    @usage('cleanup')
    @upgrade_rwlock
    def do_cleanup(self, cmd):
        """Run 'tabadmin cleanup'."""

        if len(cmd.args) != 0:
            self.print_usage(self.do_cleanup.__usage__)
            return

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        aconn = agent.connection
        if not aconn.user_action_lock(blocking=False):
            self.error(clierror.ERROR_BUSY)
            return

        stateman = self.server.state_manager
        main_state = stateman.get_state()
        if main_state in (StateManager.STATE_STARTED,
                                        StateManager.STATE_DEGRADED):
            stateman.update(StateManager.STATE_STARTED_CLEANUP)
        elif main_state in (StateManager.STATE_STOPPED,
                            StateManager.STATE_STOPPED_UNEXPECTED):
            stateman.update(StateManager.STATE_STOPPED_CLEANUP)
        else:
            self.error(clierror.ERROR_WRONG_STATE,
                       "FAIL: Main state is " + main_state)
            aconn.user_action_unlock()
            return

        if cmd.dict.has_key('userid'):
            userid = int(cmd.dict['userid'])
        else:
            userid = None

        self.ack()

        body = self.server.cleanup_cmd(agent, userid=userid)

        stateman.update(main_state)
        aconn.user_action_unlock()

        self.report_status(body)
        # Events are generated in cleanup_cmd

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
                if error_on_no_agent:
                    if not agent:
                        self.error(clierror.ERROR_AGENT_NOT_CONNECTED,
                               "No connected agent with uuid=%s" % (uuid))
            elif error_on_no_agent:
                self.error(clierror.ERROR_AGENT_NOT_SPECIFIED)
        else: # should never happen
            if error_on_no_agent:
                self.error(clierror.ERROR_AGENT_NOT_SPECIFIED)

        if agent:
            temp_agent = Agent.get_by_uuid(opts['envid'], agent.uuid)
            make_transient(temp_agent)
            if temp_agent == None:
                self.error(clierror.ERROR_AGENT_NOT_FOUND, "uuid: %s" % uuid)
                agent = None
            elif not temp_agent.enabled:
                agent = None
                if error_on_no_agent:
                    self.error(clierror.ERROR_AGENT_NOT_ENABLED,
                               "Agent disabled with uuid=%s" % (uuid))

        return agent


    def handle_exception(self, before_state, telnet_command):
        self.server.log.exception("Command Failed with Exception:")
        line = "Command Failed with Exception.\n" + \
            "Command: '%s'\n" % telnet_command

        # If the database had an internal error, etc. this may
        # be needed:
        session = meta.Session()
        session.rollback()

        line += "State is '%s'.\n" %  before_state

        line += traceback_string(all_on_one_line=False)
        self.error(clierror.ERROR_COMMAND_FAILED, line)
        self.server.event_control.gen(EventControl.SYSTEM_EXCEPTION,
                                      {'error': line,
                                       'version': self.server.version})

    def handle(self):
        while True:
            try:
                data = self.rfile.readline().strip()
            except socket.error as ex:
                self.error(clierror.ERROR_SOCKET_DISCONNECTED,
                    "CliHandler: telnet socket failure/disconnect: " + str(ex))
                break

            if not data:
                break

            self.server.log.debug("telnet command: '%s'", data)
            stateman = self.server.state_manager
            before_state = stateman.get_state()

            try:
                cmd = Command(self.server, data)
            except CommandException, ex:
                self.error(clierror.ERROR_COMMAND_SYNTAX_ERROR, str(ex))
                continue
            except (SystemExit, KeyboardInterrupt, GeneratorExit):
                raise
            except BaseException:
                self.handle_exception(before_state, data)
                self.server.log.error("Fatal: Exiting clihandler command " + \
                                      " parse '%s' on exception.", data)
                # pylint: disable=protected-access
                os._exit(91)

            if not hasattr(self, 'do_'+cmd.name):
                self.error(clierror.ERROR_NO_SUCH_COMMAND,
                           'invalid command: %s', cmd.name)
                continue

            # <command> /displayname=X /type=..., /uuid=Y, /hostname=Z [args]
            session = meta.Session()
            try:
                f = getattr(self, 'do_'+cmd.name)
                f(cmd)
            # fixme on exceptions: reset state?
            except (SystemExit, KeyboardInterrupt, GeneratorExit):
                raise
            except exc.InvalidStateError, ex:
                self.error(clierror.ERROR_WRONG_STATE, ex.message)
            except BaseException:
                self.handle_exception(before_state, data)
                self.server.log.error("Fatal: Exiting clihandler command " + \
                                      "'%s' on exception.", data)
                # pylint: disable=protected-access
                os._exit(92)
            finally:
                session.rollback()
                meta.Session.remove()
