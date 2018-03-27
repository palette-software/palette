import logging
import inspect
import sys
import os
import shlex
import SocketServer as socketserver
import socket
import json
import time
from datetime import datetime
import traceback
import subprocess
from urlparse import urlparse, urlsplit
import unicodedata

import sqlalchemy
from sqlalchemy.orm.session import make_transient

import akiri.framework.sqlalchemy as meta

from agent import Agent
from agentmanager import AgentManager
from domain import Domain
from event_control import EventControl
from files import FileManager
from get_file import GetFile
from cloud import CloudManager, CloudEntry
#from package import PackageException
from system import SystemKeys
from state import StateManager
from state_control import StateControl
from tableau import TableauProcess

import exc
import httplib
import clierror
from util import success, failed, traceback_string, upgrade_rwlock
from util import is_cloud_url

logger = logging.getLogger()

# pylint: disable=too-many-public-methods

def usage(msg):
    def wrapper(f):
        def realf(*args, **kwargs):
            return f(*args, **kwargs)
        realf.__name__ = f.__name__
        if hasattr(f, '__doc__'):
            realf.__doc__ = f.__doc__
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
        self.system = server.system
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
            entry = Domain.getone()
            opts['domainid'] = entry.domainid
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

    SUPPORT_CRON_FILENAME = "support-control"
    CRON_DIR = "/etc/cron.d"

    AUTO_UPDATE_CRON_FILENAME = "palette-update"

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

        # sockets don't do well with unicode.
        if isinstance(line, unicode):
            line = unicodedata.normalize('NFKD', line).encode('ascii', 'ignore')

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

        try:
            string = json.dumps(body, ensure_ascii=False)
        except StandardError as ex:
            logger.error("report_status json.dumps failed with: %s.  dict: %s",
                         str(ex), str(body))
            string = \
                "{'status': '%s', 'error': 'json decode error.  See log.'}" % \
                 CliHandler.STATUS_ERROR

        self.print_client("%s", string)

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
        body = self.server.cli_cmd("tabadmin status -v", agent, timeout=60*30)
        self.report_status(body)

    @usage('support [ on | off ]')
    def do_support(self, cmd):

        body = {}
        support_enabled = self.server.system[SystemKeys.SUPPORT_ENABLED]
        if not len(cmd.args):
            self.ack()
            body['enabled'] = support_enabled
            body['status'] = 'OK'
            self.report_status(body)
            return

        action = cmd.args[0].lower()
        if len(cmd.args) > 1 or action not in ('on', 'off'):
            self.print_usage(self.do_support.__usage__)
            return

        self.ack()

        if action == 'on':
            self._create_cron(self.SUPPORT_CRON_FILENAME,
                        "# Every 5 minutes.\n"
                        "*/5 * * * *   root    "
                        "test -x /usr/bin/support-control && "
                        "/usr/bin/support-control > /dev/null 2>&1\n")
            support_state = 'yes'
        else:
            self._remove_cron(self.SUPPORT_CRON_FILENAME)
            support_state = 'no'

        self.server.system.save(SystemKeys.SUPPORT_ENABLED, support_state)
        body['enabled'] = support_state

        self.report_status(body)

    def _cronpath(self, cron_filename):
        return os.path.join(self.CRON_DIR, cron_filename)

    def _create_cron(self, cron_filename, contents):
        path = self._cronpath(cron_filename)
        cronfd = open(path, "w", 0600)
        cronfd.write(contents)
        cronfd.close()

    def _remove_cron(self, cron_filename):
        path = self._cronpath(cron_filename)
        if not os.path.exists(path):
            return
        os.unlink(path)

    @usage('test email [recipient-email-address]')
    def do_test(self, cmd):
        if len(cmd.args) < 1:
            self.print_usage(self.do_test.__usage__)
            return

        action = cmd.args[0].lower()
        if action != 'email' or len(cmd.args) > 2:
            self.print_usage(self.do_test.__usage__)
            return

        if len(cmd.args) == 2:
            recipient = cmd.args[1]
        else:
            recipient = None

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
            self.server.event_control.alert_email.send(event_entry, data,
                                                       recipient)
        except StandardError:
            logger.exception('CliHandler exception:')
            self.error(clierror.ERROR_COMMAND_FAILED, traceback_string())
            return

        self.report_status({})

    @usage('timezone [update]')
    def do_timezone(self, cmd):
        """Reset/reread the current python timezone setting."""
        if len(cmd.args) and cmd.args[0] != 'update':
            self.print_usage(self.do_test.__usage__)
            return

        self.ack()
        time.tzset()
        cmd = ['/sbin/restart', 'cron']
        body = self._runcmd(cmd)
        self.report_status(body)

    @usage('upgrade [on | off | list | apt-get-update | controller | '
           'auto-on | auto-off]')
    def do_upgrade(self, cmd):
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-branches

        # Potentially update log level
        logger.setLevel(self.server.system[SystemKeys.DEBUG_LEVEL])

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

        if cmd.args[0] not in ('on', 'off', 'list', 'apt-get-update',
                               'controller', 'auto-on', 'auto-off'):
            self.print_usage(self.do_upgrade.__usage__)
            return

        if cmd.args[0] in ("list", "apt-get-update", "controller"):
            self.ack()
            self._upgrade_controller(cmd.args[0])
            return

        if cmd.args[0] in ('auto-on', 'auto-off'):
            self.ack()
            self._auto_update_controller(cmd.args[0])
            return

        # Note: an agent doesn't have to be connected to change upgrade mode.
        if cmd.args[0] == 'on':
            logger.debug("Attempting to acquire the upgrade WRITE lock.")
            self.server.upgrade_rwlock.write_acquire()
            logger.debug("Acquired the upgrade WRITE lock.")

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
                logger.debug(msg)

                self.server.upgrade_rwlock.write_release()

                return

            combined_status = {}
            if self.server.maint_started:
                combined_status['maint-stop'] = \
                                self.server.maint('stop', send_alert=False)
            combined_status['archive-stop'] = self.server.archive('stop')

            self.server.system.save(SystemKeys.UPGRADING, True)

            self.ack()
            self.report_status(combined_status)
            return

        # Disable upgrade
        self.server.system.save(SystemKeys.UPGRADING, False)
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
            logger.debug("FAIL: Can't disable upgrade: " + \
                         "upgrading: %s, " + \
                         "main state: %s, " + \
                         "error: %s",
                         stateman.upgrading(),
                         main_state,
                         str(ex))
            return

        combined_status = {}
        combined_status['archive-start'] = self.server.archive('start')
        self.ack()
        self.report_status(combined_status)

    def _auto_update_controller(self, action):
        body = {}
        if action == 'auto-on':
            self._create_cron(self.AUTO_UPDATE_CRON_FILENAME,
                        "# Every morning at 6:15 AM.\n"
                        "15 6 * * *   root    test -x "
                        "/usr/sbin/palette-update && "
                        "/usr/sbin/palette-update > /dev/null 2>&1")
            auto_update = True
        else:
            self._remove_cron(self.AUTO_UPDATE_CRON_FILENAME)
            auto_update = False

        self.server.system.save(SystemKeys.AUTO_UPDATE_ENABLED, auto_update)
        body['auto-update-enabled'] = auto_update

        self.report_status(body)

    def _upgrade_controller(self, cmd):
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        """Handle the "upgrade list", "apt-get-update" and "upgrade controller"
           commands that deal with the controller (not the agent).
        """

        if cmd != 'list':
            if os.geteuid():
                self.error(clierror.ERROR_PERMISSION,
                           "You must be super-user to run 'apt-get update'.")
                return

        if cmd == 'list':
            try:
                packages = self.server.package.list_packages()
            except PackageException as ex:
                self.error(clierror.ERROR_COMMAND_FAILED, str(ex))
                return

            self.report_status(self._package_info(packages))
            return
        elif cmd == 'apt-get-update':
            try:
                packages = self.server.package.apt_get_update()
            except PackageException as ex:
                self.error(clierror.ERROR_COMMAND_FAILED, str(ex))
                return

            self.report_status(self._package_info(packages))
            return
        elif cmd == 'controller':
            logger.debug("upgrade controller: Attempting to " + \
                         "acquire the upgrade WRITE lock.")
            try:
                self.server.upgrade_rwlock.write_acquire()
                logger.debug("upgrade: Acquired the upgrade WRITE lock.")

                logger.info("Upgrading the controller.")
                cmd = "nohup /usr/sbin/palette-update --now &"
                process = subprocess.Popen(cmd,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               preexec_fn=os.setpgrp,
                               shell=True,
                               close_fds=True)
                stdout, stderr = process.communicate()
                body = {'command': cmd}
                if process.returncode == 0:
                    body['status'] = 'OK'
                    body['exit-status'] = 0
                else:
                    body['status'] = 'FAILED'
                    body['error'] = "command failed"
                    body['exit-status'] = process.returncode

                if stdout:
                    body['stdout'] = stdout
                if stderr:
                    body['stderr'] = stderr

                self.report_status(body)
                logger.debug("upgrade_controller result: %s", str(body))
                return
            finally:
                self.server.upgrade_rwlock.write_release()

        self.error(clierror.ERROR_INTERNAL, "command: " + cmd)

    def _package_info(self, packages):
        """Take a dictionary of packages and return a dictionary with
           the controller and palette versions.
       """

        data = {}
        if packages['controller'].installed:
            data['controller-version-installed'] = \
                            packages['controller'].installed.version

        if packages['controller'].candidate:
            data['controller-version-candidate'] = \
                            packages['controller'].candidate.version

        if packages['palette'].installed:
            data['palette-version-installed'] = \
                            packages['palette'].installed.version

        if packages['palette'].candidate:
            data['palette-version-candidate'] = \
                            packages['palette'].candidate.version

        return data

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

        if cmd.dict.has_key('userid'):
            userid = int(cmd.dict['userid'])
        else:
            userid = None
            if self.server.system[SystemKeys.BACKUP_AUTO_RETAIN_COUNT] == 0:
                self.ack()
                self.report_status({'status': 'OK',
                                     'info': 'Scheduled backups are disabled'})
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
            logger.debug("Can't backup - main state is: " + main_state)
            aconn.user_action_unlock()
            return

        reported_status = self.server.statusmon.get_tableau_status()
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
            logger.debug(msg)
            aconn.user_action_unlock()
            return

        logger.debug("---------------Starting Backup-----------------")
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
            logger.exception("Backup Exception:")
            line = "Backup Error. Traceback: %s" % traceback_string()
            body = {'error': line, 'info': 'Failure'}

        # delete/rotate old backups
        rotate_info = self.server.rotate_backups()
        if 'info' in body:
            body['info'] += rotate_info
        else:
            body['info'] = rotate_info

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

        # This triggers the UI to allow the user to do another command
        stateman.update(main_state)

        # This allows another telnet command
        aconn.user_action_unlock()

        if success(body):
            entry = self.server.files.get_by_id(body['fileid'])
            body = entry.api()
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
        body = self.server.files.delfile_cmd(entry)

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
        logger.debug("do_workbook result: %s", str(body))
        self.report_status(body)

    @usage('datasource [IMPORT|FIXUP]')
    @upgrade_rwlock
    def do_datasource(self, cmd):
        """Import datasources table from Tableau or fixup a previous import"""

        if len(cmd.args) != 1:
            self.print_usage(self.do_datasource.__usage__)
            return

        action = cmd.args[0].lower()
        if action != 'import' and action != 'fixup':
            self.print_usage(self.do_datasource.__usage__)
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
            body = self.server.datasources.load(agent)
        elif action == 'fixup':
            body = self.server.datasources.fixup(agent)
        logger.debug("do_datasource result: %s", str(body))
        self.report_status(body)


    @usage('extract [IMPORT|ARCHIVE]')
    @upgrade_rwlock
    def do_extract(self, cmd):
        """import: Import extracts "from the background_jobs table in Tableau
           archive: Archive extract refreshes
        """

        # Reserved for later expansion
        if len(cmd.args) != 1:
            self.print_usage(self.do_extract.__usage__)
            return

        action = cmd.args[0].lower()
        if action not in ('import', 'archive'):
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
        if action == 'import':
            body = self.server.extract.load(agent)
        elif action == 'archive':
            body = self.server.extract_archive.refresh(agent)
        self.report_status(body)


    @usage('[/noconfig] [/nobackup] [/nolicense] restore backup-name ' + \
           '[tableau-run-as-user-password]')
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

        if not len(cmd.args) or len(cmd.args) > 2:
            self.print_usage(self.do_restore.__usage__)
            return

        backup_name = cmd.args[0]

        if len(cmd.args) == 2:
            user_password = cmd.args[1]
        else:
            user_password = None

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        aconn = agent.connection

        if cmd.dict.has_key('userid'):
            userid = int(cmd.dict['userid'])
        else:
            userid = None

        if cmd.dict.has_key('nobackup'):
            backup_first = False
        else:
            backup_first = True

        if cmd.dict.has_key('nolicense'):
            license_check = False
        else:
            license_check = True

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
            logger.debug(msg)
            aconn.user_action_unlock()
            return

        data = agent.todict()

        if cmd.dict.has_key('noconfig'):
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
            logger.debug(str(ex))
            body = {'stderr': ex, 'stdout':"", "error":""}
            self.server.event_control.gen(EventControl.RESTORE_FAILED,
                                          dict(body.items() + data.items()),
                                          userid=userid)

            aconn.user_action_unlock()
            return

        reported_status = self.server.statusmon.get_tableau_status()
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
            logger.debug(msg)
            aconn.user_action_unlock()
            return

        self.ack()

        if license_check:
            # Before we do anything, do a license check, which automatically
            # sends an event if appropriate.
            license_body = self.server.license_manager.check(agent)
            if failed(license_body):
                stateman.update(main_state)
                self.report_status(license_body)
                aconn.user_action_unlock()
                return

        if backup_first:
            # No alerts or state updates are done in backup_cmd().
            #FIXME: refactor do_backup() into do_backup() and backup()
            logger.debug("----------Starting Backup for Restore----------")
            self.server.event_control.gen(
                EventControl.BACKUP_BEFORE_RESTORE_STARTED, data, userid=userid)

            try:
                body = self.server.backup_cmd(agent, userid)
            except StandardError:
                logger.exception("Backup for Restore Exception:")
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

                if 'copy-failed' in body:
                    self.report_status(body)
                    stateman.update(main_state)
                    aconn.user_action_unlock()
                    return
            else:
                self.server.event_control.gen(
                    EventControl.BACKUP_BEFORE_RESTORE_FAILED,
                    dict(body.items() + data.items()),
                    userid=userid)

                self.report_status(body)
                stateman.update(main_state)
                aconn.user_action_unlock()
                return

        logger.debug("-------------Starting Restore---------------")

        # restore_cmd() updates the state correctly depending on the
        # success of backup, copy, stop, restore, etc.
        try:
            body = self.server.restore_cmd(agent, backup_name, main_state,
                                            no_config=no_config, userid=userid,
                                            user_password=user_password)
        except StandardError:
            stateman.update(main_state)
            logger.exception("Restore Exception:")
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

            # Restore finished successfully.
            self.server.statusmon.check_status_with_connection(agent)

            self.server.event_control.gen(EventControl.RESTORE_FINISHED,
                                          dict(body.items() + data.items()),
                                          userid=userid)
        else:
            self.server.statusmon.check_status_with_connection(agent)

            self.server.event_control.gen(EventControl.RESTORE_FAILED,
                                          dict(body.items() + data.items()),
                                          userid=userid)

        aconn.user_action_unlock()
        self.report_status(body)

    @usage('[/noconfig] restore-url <url> [tableau-run-as-user-password]')
    @upgrade_rwlock
    def do_restore_url(self, cmd):
        if not len(cmd.args) or len(cmd.args) > 2:
            self.print_usage(self.do_restore_url.__usage__)
            return

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        url = urlsplit(cmd.args[0])
        if not url.scheme in ('file', 's3', 'gs'):
            self.error(clierror.ERROR_BAD_VALUE,
                       "Invalid URL scheme : '%s'" % (url.scheme,))
            return

        # Take the user action lock before checking state
        agent.connection.user_action_lock()

        # Check to see if we're in a state to restore
        main_state = self.server.state_manager.get_state()
        if main_state not in (StateManager.STATE_STARTED,
                              StateManager.STATE_DEGRADED,
                              StateManager.STATE_STOPPED,
                              StateManager.STATE_STOPPED_UNEXPECTED):
            self.error(clierror.ERROR_WRONG_STATE,
                       "Invalid restore state: " + main_state)
            agent.connection.user_action_unlock()
            return

        self.ack()

        kwargs = {}
        if len(cmd.args) == 2:
            kwargs['run_as_password'] = cmd.args[1]

        if cmd.dict.has_key('userid'):
            userid = int(cmd.dict['userid'])
            kwargs['userid'] = userid
        else:
            userid = None

        if cmd.dict.has_key('noconfig'):
            kwargs['data_only'] = True

        logger.debug("-----------Starting Restore (URL)-------------")
        try:
            body = self.server.restore_url(agent, url, **kwargs)
        except StandardError:
            logger.exception("Restore Exception:")
            line = "Restore Error: Traceback: %s" % traceback_string()
            body = {'error': line}

        self.server.statusmon.check_status_with_connection(agent)

        data = agent.todict()
        if success(body):
            # Restore finished successfully.
            self.server.event_control.gen(EventControl.RESTORE_FINISHED,
                                          dict(body.items() + data.items()),
                                          userid=userid)
        else:
            self.server.event_control.gen(EventControl.RESTORE_FAILED,
                                          dict(body.items() + data.items()),
                                          userid=userid)
        agent.connection.user_action_unlock()
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

    @usage('[/timeout=<seconds>] cli <command> [args...]')
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
        if cmd.dict.has_key('timeout'):
            try:
                timeout = int(cmd.dict['timeout'])
            except ValueError, ex:
                self.error(clierror.ERROR_INVALID_PORT,
                           "cli: Invalid timeout: " + str(ex))
                return
            body = self.server.cli_cmd(cli_command, agent, timeout=timeout)
        else:
            body = self.server.cli_cmd(cli_command, agent)
        self.report_status(body)

    @usage('kill <xid>')
    def do_kill(self, cmd):

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        if len(cmd.args) != 1:
            self.print_usage(self.do_kill.__usage__)
            return

        try:
            xid = int(cmd.args[0])
        except ValueError:
            self.error(clierror.ERROR_INVALID_XID,
                       "Invalid XID: " + cmd.args[0])
            return

        self.ack()
        body = self.server.kill_cmd(xid, agent)
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

        body = self.server.cli_cmd(phttp_cmd, agent, env=env, timeout=10*60)
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
                logger.info("pinfo failed: %s", str(ex))
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
                logger.info("pinfo failed for agent '%s': %s",
                            agent.displayname, str(ex))
                return

            pinfos.append(body)

        self.report_status({"info": pinfos})

    @usage('info2 [all]')
    @upgrade_rwlock
    def do_info2(self, cmd):
        # pylint: disable=too-many-return-statements
        """Generate system info using the /info primitive."""
        if len(cmd.args) == 1:
            if cmd.args[0] != 'all':
                self.print_usage(self.do_info2.__usage__)
                return
        elif len(cmd.args) > 2:
            self.print_usage(self.do_info2.__usage__)
            return

        if not len(cmd.args):
            agent = self.get_agent(cmd.dict)
            if not agent:
                return

            self.ack()
            try:
                body = self.server.get_info(agent, update_agent=True)
            except IOError as ex:
                self.error(clierror.ERROR_COMMAND_FAILED, str(ex))
                logger.info("info failed: %s", str(ex))
                return

            self.report_status(body)
            return

        self.ack()

        agents = self.server.agentmanager.all_agents()
        if len(agents) == 0:
            self.report_status({})
            return

        infos = []
        for key in agents.keys():
            try:
                agent = agents[key]
            except StandardError:
                # This agent is now gone
                continue

            try:
                body = self.server.get_info(agent, update_agent=True)
            except IOError as ex:
                self.error(clierror.ERROR_COMMAND_FAILED, str(ex))
                logger.info("info failed for agent '%s': %s",
                            agent.displayname, str(ex))
                return

            infos.append(body)

        self.report_status({"info": infos})

    @usage('license [update | info | {verify|send} | repair]')
    @upgrade_rwlock
    def do_license(self, cmd):
        """Run license check."""
        action = 'update'
        if len(cmd.args) > 1:
            self.print_usage(self.do_license.__usage__)
            return
        if len(cmd.args) == 1:
            action = cmd.args[0].lower()
            if not action in ['repair', 'info', 'verify', 'send', 'update']:
                self.print_usage(self.do_license.__usage__)
                return

        state = self.server.state_manager.get_state()
        if action not in ['info', 'verify', 'send']:
            agent = self.get_agent(cmd.dict)
            if not agent:
                self.error(clierror.ERROR_AGENT_NOT_CONNECTED,
                       "FAIL: Main state is " + state)
                return

        if not self.server.odbc_ok() and action not in ['info', 'verify',
                                                            'send', 'repair']:
            self.error(clierror.ERROR_WRONG_STATE,
                       "FAIL: Main state is " + state)
            return

        self.ack()
        if action == 'repair':
            body = self.server.license_manager.repair(agent)
        elif action == 'update':
            body = self.server.license_manager.check(agent)
        elif action == 'info':
            body = self.server.license_manager.info()
            # convert expiration-time and contact-time to strings
            body = self._json_sanity(body)
        elif action in ('verify', 'send'):
            body = self.server.license_manager.send()
        else:
            self.print_usage(self.do_license.__usage__)
        self.report_status(body)

    def _json_sanity(self, jdict):
        """Convert any non-json-dumpable values to string.
           fixme: Generalize and call from report_status()."""
        for key in jdict:
            if type(jdict[key]) not in [int, str]:
                jdict[key] = str(jdict[key])

        return jdict

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
            logger.debug("FAIL: Can't get yml: %s", str(ex))
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

    @usage('metric')
    @upgrade_rwlock
    def do_metric(self, cmd):
        """Check on metrics and potentially send an alert."""

        if len(cmd.args):
            self.print_usage(self.do_metric.__usage__)
            return

        self.ack()

        body = self.server.metrics.check()

        self.report_status(body)

    @usage('prune')
    @upgrade_rwlock
    def do_prune(self, cmd):
        """Prune old rows from the metrics table."""

        if len(cmd.args):
            self.print_usage(self.do_prune.__usage__)
            return

        self.ack()

        body = self.server.metrics.prune()

        self.report_status(body)

    @usage('daily')
    def do_daily(self, cmd):
        """Do daily emails, etc."""

        if len(cmd.args):
            self.print_usage(self.do_daily.__usage__)
            return

        self.ack()

        data = {'emailed-reminder': False}

        entry = self.server.system.entry(SystemKeys.EMAIL_SPIKE_DISABLED_ALERTS)
        if not entry or not entry.typed():
            self.report_status(data)
            return

        timedelta = datetime.utcnow() - entry.modification_time

        data['days_elapsed'] = timedelta.days
        # Don't remind them  until at least one day has elapsed since
        # they received the EMAIL SPIKE event.
        if timedelta.days >= 1:
            data['emailed-reminder'] = True
            if timedelta.days > 1:
                data['days_plural'] = 's'
            else:
                data['days_plural'] = ''
            self.server.event_control.gen(EventControl.EMAIL_DISABLED_REMINDER,
                                          data)

        # fixme: convert _ to -
        self.report_status(data)

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

        reported_status = self.server.statusmon.get_tableau_status()
        if reported_status != TableauProcess.STATUS_STOPPED:
            self.error(clierror.ERROR_WRONG_STATE,
                       "Can't start - reported status is: " + reported_status)
            aconn.user_action_unlock()
            return

        stateman.update(StateManager.STATE_STARTING)

        logger.debug("--------------Starting Tableau----------------")
        # fixme: Reply with "OK" only after the agent received the command?
        self.ack()

        if cmd.dict.has_key('userid'):
            userid = int(cmd.dict['userid'])
        else:
            userid = None

        # If the maintenance web server is started, stop the maintenance web
        # server relinquish the web server port before tabadmin start tries
        # to listen on the web server port.

        if self.server.maint_started:
            self.server.maint("stop")
        # FIXME: let it continue ?

        body = self.server.cli_cmd('tabadmin start', agent, timeout=60*60)
        if body.has_key("exit-status"):
            exit_status = body['exit-status']
        else:
            exit_status = 1 # if no 'exit-status' then consider it failed.

        self.server.statusmon.check_status_with_connection(agent)

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
                                          dict(body.items() + data.items()),
                                          userid=userid)

        aconn.user_action_unlock()

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

        reported_status = self.server.statusmon.get_tableau_status()
        if reported_status not in good_reported_status:
            msg = "Can't stop/restart - reported status is: " + reported_status
            self.error(clierror.ERROR_WRONG_STATE, "FAIL: " + msg)
            logger.debug(msg)
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
            logger.debug("-----------Starting Backup before %s--------------",
                         action)
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
                stateman.update(main_state)
                self.report_status(body)
                aconn.user_action_unlock()
                return False

        return True

    @usage('[/nobackup] [/nolicense] restart')
    @upgrade_rwlock
    def do_restart(self, cmd):
        if len(cmd.args):
            self.print_usage(self.do_restart.__usage__)
            return

        if cmd.dict.has_key('nobackup'):
            backup_first = False
        else:
            backup_first = True

        if cmd.dict.has_key('nolicense'):
            license_check = False
        else:
            license_check = True

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

        logger.debug("-------------Restarting Tableau----------------")
        data = agent.todict()
        self.server.event_control.gen(EventControl.RESTART_STARTED, data,
                                      userid=userid)

        # fixme: Reply with "OK" only after the agent received the command?
        body = self.server.cli_cmd('tabadmin restart', agent, timeout=60*60)


        if success(body):
            stateman.update(StateManager.STATE_STARTED)
            self.server.event_control.gen(EventControl.RESTART_FINISHED,
                                          dict(body.items() + data.items()),
                                          userid=userid)
            aconn.user_action_unlock()
            # Trigger getting current status from Tableau
            self.server.agentmanager.trigger_check_status_event()
        else:
            self.server.event_control.gen(EventControl.RESTART_FAILED,
                                          dict(body.items() + data.items()),
                                          userid=userid)
            # Get the latest status from tabadmin which sets the main state.
            self.server.statusmon.check_status_with_connection(agent)

            aconn.user_action_unlock()

        self.report_status(body)

    @usage('[/nobackup] [/nolicense] [/nomaint] stop')
    @upgrade_rwlock
    def do_stop(self, cmd):
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements

        if len(cmd.args):
            self.print_usage(self.do_stop.__usage__)
            return

        if cmd.dict.has_key('userid'):
            userid = int(cmd.dict['userid'])
        else:
            userid = None

        if cmd.dict.has_key('nobackup'):
            backup_first = False
        else:
            backup_first = True

        if cmd.dict.has_key('nolicense'):
            license_check = False
        else:
            license_check = True

        if cmd.dict.has_key('nomaint'):
            start_maint = False
        else:
            start_maint = True

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

        logger.debug("--------------Stopping Tableau-----------------")
        # fixme: Reply with "OK" only after the agent received the command?
        body = self.server.cli_cmd('tabadmin stop', agent, timeout=60*30)
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

        self.server.statusmon.check_status_with_connection(agent)
        if success(body):
            self.server.event_control.gen(EventControl.STATE_STOPPED,
                                      agent.todict(), userid=userid)

        # fixme: Add STOP_FAILED event?
        aconn.user_action_unlock()
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

    @usage('exit')
    def do_exit(self, cmd):
        """Clean exit the controller."""
        if len(cmd.args) > 0:
            self.print_usage(self.do_exit.__usage__)
            return
        self.ack()
        # pylint: disable=protected-access
        os._exit(0)

    def _runcmd(self, cmd):
        process = subprocess.Popen(cmd,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   close_fds=True)
        stdout, stderr = process.communicate()
        body = {'command': ' '.join(cmd)}
        if process.returncode == 0:
            body['status'] = 'OK'
            body['exit-status'] = 0
        else:
            body['status'] = 'FAILED'
            body['error'] = "command failed"
            body['exit-status'] = process.returncode

        if stdout:
            body['stdout'] = stdout
        if stderr:
            body['stderr'] = stderr

        return body

    @usage('apache [start|stop|restart|reload|force-reload')
    def do_apache(self, cmd):
        """Control the apache2 service. (must be run as root)"""
        if len(cmd.args) != 1:
            self.print_usage(self.do_apache.__usage__)
            return
        action = cmd.args[0].lower()
        if action not in ['start', 'stop', 'restart', 'reload', 'force-reload']:
            self.print_usage(self.do_apache.__usage__)
            return
        if os.geteuid() != 0:
            self.error(clierror.ERROR_PERMISSION)
            return
        self.ack()

        cmd = ['/usr/sbin/service', 'apache2', action]
        body = self._runcmd(cmd)
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

        body = self.server.archive(action, agent, port)
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


    @usage('file [GET|PUT|DELETE|SHA256|MOVE|LISTDIR|SIZE|MKDIRS|TYPE|WRITE]' +\
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
                body = agent.filemanager.delete(path)
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
            elif method == 'TYPE':
                if len(cmd.args) != 2:
                    self.print_usage(self.do_file.__usage__)
                    return
                self.ack()
                body = agent.filemanager.filetype(path)
            elif method == 'WRITE':
                self.ack()
                body = agent.filemanager.put(path, cmd.args[2])
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

    @usage('cloud GET <s3://url>|<gs://url> [agent-download-dir]')
    def do_cloud(self, cmd):
        """This is a newer interface that GETs a file from cloud storage -
        s3 or gcs - and downloads it to the agent.
        The file is specified by a (cloud) url.
        """
        pwd = None
        if len(cmd.args) < 2:
            self.print_usage(self.do_cloud.__usage__)
            return
        if len(cmd.args) == 3:
            pwd = cmd.args[2]
        elif len(cmd.args) > 3:
            self.print_usage(self.do_cloud.__usage__)
            return

        action = cmd.args[0].upper()
        if action != 'GET':
            self.print_usage(self.do_cloud.__usage__)
            return
        url = cmd.args[1]
        if not is_cloud_url(url):
            self.print_usage(self.do_cloud.__usage__)
            return

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        self.ack()
        try:
            body = self.server.cloud.download(agent, url, pwd=pwd)
        except ValueError, ex:
            self.error(clierror.ERROR_BAD_VALUE, ex.message)
            return
        self.report_status(body)

    def _do_cloud_test(self, cloud_type, cmd):
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        """Test cloud credentials/commands by putting and then
           deleting a file on cloud storage of "cloud_type"."""
        if cloud_type == CloudManager.CLOUD_TYPE_S3:
            cloud_type_id = SystemKeys.S3_ID
            cloud_instance = self.server.cloud.s3
        elif cloud_type == CloudManager.CLOUD_TYPE_GCS:
            cloud_type_id = SystemKeys.GCS_ID
            cloud_instance = self.server.cloud.gcs
        else:
            raise ValueError('cloud_type')

        option_count = 0
        for option in ['access-key', 'secret-key', 'bucket']:
            if option in cmd.dict:
                option_count += 1

        if option_count:
            if option_count != 3:
                self.error(clierror.ERROR_COMMAND_SYNTAX_ERROR,
                   "Credentials require all of: /access-key, /secret-key " + \
                   "and /bucket.")
                return

            # Create a temporary, in-memory cloud entry just for
            # testing the cloud connection.
            entry = CloudEntry(cloud_type=cloud_type,
                               name=cmd.dict['bucket'],
                               bucket=cmd.dict['bucket'],
                               access_key=cmd.dict['access-key'],
                               secret=cmd.dict['secret-key'])
        else:
            entry = self.server.cloud.get_cloud_entry(cloud_type_id)
            if not entry:
                self.error(clierror.ERROR_COMMAND_FAILED,
                           "No cloud credentials saved for cloud type %s" % \
                           cloud_type)
                return

        agent = self.server.agentmanager.agent_by_type(
                                            AgentManager.AGENT_TYPE_PRIMARY)
        if not agent:
            self.error(clierror.ERROR_AGENT_NOT_CONNECTED,
                       "Primary agent must be connected for 'test' command.")
            return

        self.ack()

        # This file must exist on the agent.
        keypath = "palette_logo.png"
        dirpath = agent.path.join(agent.install_dir, "maint", "www", "image")
        body = cloud_instance.put(agent, entry, keypath, pwd=dirpath)
        if failed(body):
            logger.info("Put to keypath '%s', dirpath '%s', " + \
                        "cloud type '%s' failed.",
                        keypath, dirpath, cloud_type)
            self.report_status(body)
            return

        try:
            delete_body = cloud_instance.delete_file(entry, keypath)
        except IOError as ex:
            delete_body = {'error': str(ex)}

        if failed(delete_body):
            logger.info("Delete path '%s', cloud type '%s' failed.",
                        keypath, cloud_type)
            self.report_status(delete_body)
            return

        self.report_status(body)

    def _do_cloud(self, cloud_type, usage_msg, cmd):
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements

        if cloud_type == CloudManager.CLOUD_TYPE_S3:
            cloud_type_id = SystemKeys.S3_ID
            cloud_instance = self.server.cloud.s3
        elif cloud_type == CloudManager.CLOUD_TYPE_GCS:
            cloud_type_id = SystemKeys.GCS_ID
            cloud_instance = self.server.cloud.gcs
        else:
            raise ValueError('cloud_type')

        if len(cmd.args) == 1 and cmd.args[0].upper() == 'TEST':
            return self._do_cloud_test(cloud_type, cmd)
        if len(cmd.args) == 2:
            dirpath = None
        elif len(cmd.args) == 3:
            dirpath = cmd.args[2]
        else:
            self.print_usage(usage_msg)
            return

        if 'bucket-subdir' in cmd.dict:
            bucket_subdir = cmd.dict['bucket-subdir']
        else:
            bucket_subdir = None

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
            cloudid = self.server.system[cloud_type_id]
            if cloudid is None:
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
            if bucket_subdir:
                cloud_path = os.path.join(bucket_subdir, keypath)
            else:
                cloud_path = keypath
            body = cloud_instance.get(agent, entry, cloud_path, pwd=dirpath)
        elif action == 'PUT':
            body = cloud_instance.put(agent, entry, keypath,
                                      bucket_subdir=bucket_subdir, pwd=dirpath)
        elif action == 'DELETE':
            if bucket_subdir:
                cloud_path = os.path.join(bucket_subdir, keypath)
            else:
                cloud_path = keypath
            try:
                body = cloud_instance.delete_file(entry, cloud_path)
            except IOError as ex:
                body['error'] = str(ex)

        self.report_status(body)

    @usage('s3 { [/name=cloud-name /bucket-subdir=SD] get filepath-key '
                '[dirpath] | '
                '[/name=cloud-name /bucket-subdir=SD] put filepath-key '
                '[dirpath] | '
                'delete bucketname filepath | '
                '[/access-key=X /secret-key=Y /bucket=Z] test }')
    def do_s3(self, cmd):
        """Send a file to or receive a file from an S3 bucket"""
        return self._do_cloud(CloudManager.CLOUD_TYPE_S3,
                              self.do_s3.__usage__,
                              cmd)

    @usage('gcs { [/name=cloud-name /bucket-subdir=SD] get filepath-key '
                '[dirpath] | '
                '[/name=cloud-name /bucket-subdir=SD] put filepath-key '
                '[dirpath] | '
                'delete bucketname filepath | '
                '[/access-key=X /secret-key=Y /bucket=Z] test }')
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
                self.server.system[key] = value
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

    @usage('support-case [filename.zip]')
    @upgrade_rwlock
    def do_support_case(self, cmd):
        """ Generate a support case and return the zip file information. """

        filename = None
        if len(cmd.args) == 1:
            filename = cmd.args[0]
        elif cmd.args:
            self.print_usage(self.do_support_case.__usage__)

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        if cmd.dict.has_key('userid'):
            userid = int(cmd.dict['userid'])
        else:
            userid = None

        self.ack()

        agent.connection.user_action_lock(blocking=False)
        body = self.server.support_case(agent, userid=userid, filename=filename)
        agent.connection.user_action_unlock()
        return self.report_status(body)

    @usage('ziplogs')
    @upgrade_rwlock
    def do_ziplogs(self, cmd):
        """Run 'tabadmin ziplogs'."""

        if len(cmd.args) != 0:
            self.print_usage(self.do_ziplogs.__usage__)
            return

        if cmd.dict.has_key('userid'):
            userid = int(cmd.dict['userid'])
        else:
            userid = None
            if self.server.system[SystemKeys.ZIPLOG_AUTO_RETAIN_COUNT] == 0:
                self.ack()
                self.report_status({'status': 'OK',
                                     'info': 'Scheduled ziplogs are disabled'})
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

        self.ack()

        body = self.server.ziplogs_cmd(agent, userid=userid)
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

    @usage('get <URL> [output-file-path]')
    def do_get(self, cmd):
        """Do an HTTP GET from the agent to the specified URL.
        The resulting files is stored on the controller.
        """
        # pylint: disable=too-many-locals
        if len(cmd.args) == 2:
            url = cmd.args[0]
            path = cmd.args[1]
        elif len(cmd.args) == 1:
            url = cmd.args[0]
            parsed_url = urlparse(url)
            path = os.path.basename(parsed_url.path)
            if not path:
                path = 'index.html'
        else:
            self.print_usage(self.do_get.__usage__)
            return

        agent = self.get_agent(cmd.dict)
        if not agent:
            return

        timeout = None
        if 'timeout' in cmd.dict:
            try:
                timeout = int(cmd.dict['timeout'])
            except StandardError:
                # FIXME
                pass

        self.ack()

        try:
            res = agent.connection.http_send_get(url, timeout=timeout)
        except (exc.HTTPException, httplib.HTTPException) as ex:
            body = {'error': str(ex)}
            self.report_status(body)
            return

        content_type = res.getheader('Content-Type', '').lower()
        headers = res.getheaders()

        logger.info("GET %s, Headers: '%s'", url, str(res.getheaders()))

        if content_type == 'application/x-json':
            # This extended type indicates the agent generated the JSON,
            # i.e. there was an error.
            data = json.loads(res.body) # FIXME: catch parse error?
            self.report_status(data)
            return

        # FIXME: catch exceptions.
        with open(path, 'w') as f:
            f.write(res.body)

        path = os.path.abspath(os.path.expanduser(path))
        data = {'status': 'OK', 'URL': url, 'path': path}
        for header, value in headers:
            data[header] = value
        self.report_status(data)

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
        logger.exception("Command Failed with Exception:")

        # Remove password if it was:
        #   ad verify username password
        # or
        #   auth verify username password
        tokens = telnet_command.split()
        if len(tokens) == 4:
            if tokens[0] in ('ad', 'auth') and tokens[1] == 'verify':
                tokens[3] = '<>'
                telnet_command = ' '.join(tokens)

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

            logger.debug("telnet command: '%s'", data)
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
                logger.error("Fatal: Exiting clihandler command " + \
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
                logger.error("Fatal: Exiting clihandler command " + \
                             "'%s' on exception.", data)
                # pylint: disable=protected-access
                os._exit(92)
            finally:
                session.rollback()
                meta.Session.remove()
