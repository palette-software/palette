#!/usr/bin/env python

import sys
import os
import SocketServer as socketserver

import json
import time
import datetime

import exc
from request import CliStartRequest, CleanupRequest

import httplib
import ntpath

import sqlalchemy
from sqlalchemy.orm import sessionmaker, scoped_session

# pylint: disable=import-error,no-name-in-module
from akiri.framework.ext.sqlalchemy import meta
# pylint: enable=import-error,no-name-in-module

# These are need for create_all().
# FIXME: these should logically go in __init__.py.
# pylint: disable=unused-import
from agentmanager import AgentManager
from agent import Agent
from agentinfo import AgentVolumesEntry, AgentYmlEntry
from alert_email import AlertEmail
from auth import AuthManager
from config import Config
from credential import CredentialEntry, CredentialManager
from diskcheck import DiskCheck, DiskException
from data_source_types import DataSourceTypes
from domain import Domain
from environment import Environment
from event_control import EventControl, EventControlManager
from extracts import ExtractManager
from files import FileManager
from firewall_manager import FirewallManager
from general import SystemConfig
from http_requests import HttpRequestEntry, HttpRequestManager
from licensing import LicenseManager, LicenseEntry
from ports import PortManager
from profile import UserProfile, Role
from sched import Sched, Crontab
from state import StateManager
from state_control import StateControl
from system import SystemManager
from tableau import TableauStatusMonitor, TableauProcess
from workbooks import WorkbookEntry, WorkbookUpdateEntry, WorkbookManager
#pylint: enable=unused-import

from sites import Site
from projects import Project
from data_connections import DataConnection

from place_file import PlaceFile
from get_file import GetFile
from cloud import CloudManager

from clihandler import CliHandler
from util import version, success, sizestr, safecmd

# pylint: disable=no-self-use

class Controller(socketserver.ThreadingMixIn, socketserver.TCPServer):
    # pylint: disable=too-many-public-methods
    # pylint: disable=too-many-instance-attributes

    CLI_URI = "/cli"
    LOGGER_NAME = "main"
    allow_reuse_address = True

    DATA_DIR = "Data"
    BACKUP_DIR = "tableau-backups"
    LOG_DIR = "tableau-logs"
    WORKBOOKS_DIR = "tableau-workbooks"
    PALETTE_DIR = "palette-system"

    STAGING_DIR = "staging"

    FILENAME_FMT = "%Y%m%d_%H%M%S"

    def backup_cmd(self, agent, userid):
        """Perform a backup - not including any necessary migration."""
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-return-statements

        if userid == None:
            auto = True     # It is an 'automatic/scheduled' backup
        else:
            auto = False    # It was requested by a specific user

        min_disk_needed = agent.tableau_data_size * .3

        # Disk space check.
        try:
            dcheck = DiskCheck(self, agent, self.BACKUP_DIR,
                               FileManager.FILE_TYPE_BACKUP, min_disk_needed)
        except DiskException, ex:
            return self.error(str(ex))

        if dcheck.target_type == FileManager.STORAGE_TYPE_CLOUD:
            self.log.debug("Backup will copy to cloud storage type %s " + \
                           "name '%s' bucket '%s'",
                            dcheck.target_entry.cloud_type,
                            dcheck.target_entry.name,
                            dcheck.target_entry.bucket)
        elif dcheck.target_type == FileManager.STORAGE_TYPE_VOL:
            if dcheck.target_entry.agentid == agent.agentid:
                self.log.debug("Backup will stay on the primary.")
            else:
                self.log.debug(
                    "Backup will copy to target '%s', target_dir '%s'",
                        dcheck.target_agent.displayname, dcheck.target_dir)
        else:
            self.log.error("backup_cmd: Invalid target_type: %s" % \
                           dcheck.target_type)
            return self.error("backup_cmd: Invalid target_type: %s" % \
                              dcheck.target_type)
        # Example name: 20140127_162225.tsbak
        backup_name = time.strftime(self.FILENAME_FMT) + ".tsbak"

        # Example: "c:/ProgramData/Palette/Data/tableau-backups/<name>.tsbak"

        # e.g. E:\\ProgramData\Palette\Data\tableau-backups\<name>.tsbak
        backup_full_path = agent.path.join(dcheck.primary_dir, backup_name)

        cmd = 'tabadmin backup \\\"%s\\\"' % backup_full_path

        backup_start_time = time.time()
        body = self.cli_cmd(cmd, agent)
        backup_elapsed_time = time.time() - backup_start_time

        if body.has_key('error'):
            body['info'] = 'Backup command elapsed time before failure: %s' % \
                            self.seconds_to_str(backup_elapsed_time)
            return body

        backup_size_body = agent.filemanager.filesize(backup_full_path)
        if not success(backup_size_body):
            self.log.error("Failed to get size of backup file %s: %s" %\
                            (backup_full_path, backup_size_body['error']))
            backup_size = 0

        else:
            backup_size = backup_size_body['size']

        # If the target is not on the primary agent, then after the
        # backup, it will be copied to either:
        #   1) another agent
        # or
        #   2) cloud storage
        place = PlaceFile(self, agent, dcheck, backup_full_path, backup_size,
                          auto)

        body['info'] = place.info
        if place.copy_failed:
            body['copy-failed'] = True

        # Report backup stats
        total_time = backup_elapsed_time + place.copy_elapsed_time

        stats = 'Backup size: %s\n' % sizestr(backup_size)
        stats += 'Backup elapsed time: %s' % \
                  (self.seconds_to_str(backup_elapsed_time))

        if place.copied:
            stats += ' (%.0f%%)\n' % ((backup_elapsed_time / total_time) * 100)
            stats += 'Backup copy elapsed time: %s (%.0f%%)\n' % \
                     (self.seconds_to_str(place.copy_elapsed_time),
                     (place.copy_elapsed_time / total_time) * 100)

            stats += 'Backup total elapsed time: %s' % \
                      self.seconds_to_str(total_time)
        else:
            stats += '\n'

        body['info'] += '\n' + stats
        return body

    def rotate_backups(self):
        """Rotate/delete old auto-generated and then user-generated
           backup files."""
        file_type = FileManager.FILE_TYPE_BACKUP
        st_config = SystemConfig(self.system)
        find_method = self.files.find_by_auto_envid
        find_name = "scheduled"

        info = self.file_rotate(st_config.backup_auto_retain_count,
                                find_method, find_name, file_type)

        find_method = self.files.find_by_non_auto_envid
        find_name = "user generated"

        info += self.file_rotate(st_config.backup_user_retain_count,
                                 find_method, find_name, file_type)

        return info

    def rotate_ziplogs(self):
        """Rotate/delete old ziplog files."""
        st_config = SystemConfig(self.system)
        find_method = self.files.all_by_type
        find_name = ""
        file_type = FileManager.FILE_TYPE_ZIPLOG

        info = self.file_rotate(st_config.log_archive_retain_count,
                                find_method, find_name, file_type)

        return info

    def file_rotate(self, retain_count, find_method, find_name, file_type):
        """Delete the old files."""

        rows = find_method(self.environment.envid, file_type)

        remove_count = len(rows) - retain_count
        if remove_count <= 0:
            remove_count = 0
            info = ""
        else:
            info = ("\nThere are %d %s %s files.  Retaining %d.  " + \
                   "Will remove %d.") % \
                   (len(rows), find_name, file_type,
                   retain_count, remove_count)

            self.log.debug(info)

        for entry in rows[:remove_count]:
            self.log.debug(
                    "file_rotate: deleting %s file type " +
                    "%s name %s fileid %d", find_name, file_type, entry.name,
                    entry.fileid)
            body = self.delfile_cmd(entry)
            if 'error' in body:
                info += '\n' + body['error']
            elif 'stderr' in body and len(body['stderr']):
                info += '\n' + body['stderr']
            else:
                if entry.storage_type == FileManager.STORAGE_TYPE_VOL:
                    info += "\nRemoved %s" % entry.name
                else:
                    cloud_entry = self.cloud.get_by_cloudid(entry.storageid)
                    if not cloud_entry:
                        info += "\nfile_rotate: cloudid not found: %d" % \
                                 entry.storageid
                    else:
                        info += "\nRemoved from %s bucket %s: %s" % \
                                (cloud_entry.cloud_type, cloud_entry.bucket,
                                 entry.name)
        return info

    def seconds_to_str(self, seconds):
        return str(datetime.timedelta(seconds=int(seconds)))

    def delfile_cmd(self, entry):
        """Delete a file, wherever it is
            Argument:
                    entry   The file entry.
        """
        # pylint: disable=too-many-return-statements

        # Delete a file from the cloud
        if entry.storage_type == FileManager.STORAGE_TYPE_CLOUD:
            try:
                self.delete_cloud_file(entry)
            except IOError as ex:
                return {'error': str(ex)}
            try:
                self.files.remove(entry.fileid)
            except sqlalchemy.orm.exc.NoResultFound:
                return {'error': ("fileid %d not found: name=%s cloudid=%d" % \
                        (entry.fileid, entry.name,
                        entry.storageid))}
            return {}

        # Delete a file from an agent.
        vol_entry = AgentVolumesEntry.get_vol_entry_by_volid(entry.storageid)
        if not vol_entry:
            return {"error": "volid not found: %d" % entry.storageid}

        target_agent = None
        agents = self.agentmanager.all_agents()
        for key in agents.keys():
            self.agentmanager.lock()
            if not agents.has_key(key):
                self.log.info(
                    "copy_cmd: agent with conn_id %d is now " + \
                    "gone and won't be checked.", key)
                self.agentmanager.unlock()
                continue
            agent = agents[key]
            self.agentmanager.unlock()

            if agent.agentid == vol_entry.agentid:
                target_agent = agent
                break

        if not target_agent:
            return {'error': "Agentid %d not connected." % vol_entry.agentid}

        file_full_path = entry.name
        self.log.debug("delfile_cmd: Deleting path '%s' on agent '%s'",
                       file_full_path, target_agent.displayname)

        body = self.delete_vol_file(target_agent, file_full_path)
        if not body.has_key('error'):
            try:
                self.files.remove(entry.fileid)
            except sqlalchemy.orm.exc.NoResultFound:
                return {'error': ("fileid %d not found: name=%s agent=%s" % \
                        (entry.fileid, file_full_path,
                        target_agent.displayname))}
        return body

    def status_cmd(self, agent):
        return self.cli_cmd('tabadmin status -v', agent)

    def cli_cmd(self, command, agent, env=None, immediate=False):
        """ 1) Sends the command (a string)
            2) Waits for status/completion.  Saves the body from the status.
            3) Sends cleanup.
            4) Returns body from the status.
        """
        # pylint: disable=too-many-return-statements

        body = self._send_cli(command, agent, env=env, immediate=immediate)

        if body.has_key('error'):
            return body

        if not body.has_key('run-status'):
            return self.error("_send_cli (%s) missing 'run-status': %s" % \
                              (safecmd(command), str(body)))

        # It is possible for the command to finish immediately.
        if body['run-status'] == 'finished':
            return body

        cli_body = self._get_cli_status(body['xid'], agent, command)

        if not 'stdout' in cli_body:
            self.log.error(
                "check status of cli xid %d failed - missing 'stdout' in " + \
                "reply for command '%s': %s", body['xid'], command, cli_body)
            if not 'error' in cli_body:
                cli_body['error'] = \
                    ("Missing 'stdout' in agent reply for xid %d, " + \
                    "command '%s': %s") % \
                    (safecmd(command), body['xid'], cli_body)

        cleanup_body = self._send_cleanup(body['xid'], agent, command)

        if cli_body.has_key("error"):
            return cli_body

        if cleanup_body.has_key('error'):
            return cleanup_body

        return cli_body

    def public_url(self):
        """ Generate a url for Tableau that is reportable to a user."""
        url = self.system.get('tableau-server-url', default=None)
        if url:
            return url

        envid = self.environment.envid

        key = 'svcmonitor.notification.smtp.canonical_url'
        url = AgentYmlEntry.get(envid, key, default=None)
        if url:
            return url

        return None

    def local_url(self):
        """ Generate a url for Tableau that the agent can use internally"""

        url = self.public_url()
        if url:
            return url

        envid = self.environment.envid

        key = 'datacollector.apache.url'
        url = AgentYmlEntry.get(envid, key, default=None)
        if url:
            tokens = url.split('/', 3)
            if len(tokens) >= 3:
                return tokens[0] + '//' + tokens[2]
        return None

    def tabcmd(self, args, agent):
        cred = self.cred.get('primary', default=None)
        if cred is None:
            cred = self.cred.get('secondary', default=None)
            if cred is None:
                errmsg = 'No credentials found.'
                self.log.error('tabcmd: ' + errmsg)
                return {'error': 'No credentials found.'}
        pw = cred.getpasswd()
        if not cred.user or not pw:
            errmsg = 'Invalid credentials.'
            self.log.error('tabcmd: ' + errmsg)
            return {'error': errmsg}
        url = self.local_url()
        if not url:
            errmsg = 'No local URL available.'
            return {'error': errmsg}
        # tabcmd options must come last.
        cmd = ('tabcmd %s -u %s --password %s ' + \
               '--no-cookie --server %s --no-certcheck ') %\
              (args, cred.user, pw, url)
        return self.cli_cmd(cmd, agent)

    def _send_cli(self, cli_command, agent, env=None, immediate=False):
        """Send a "cli" command to an Agent.
            Returns a body with the results.
            Called without the connection lock."""
        # pylint: disable=too-many-return-statements

        self.log.debug("_send_cli")

        aconn = agent.connection
        aconn.lock()

        req = CliStartRequest(cli_command, env=env, immediate=immediate)

        headers = {"Content-Type": "application/json"}
        uri = self.CLI_URI

        displayname = agent.displayname and agent.displayname or agent.uuid
        self.log.debug(
            "about to send the cli command to '%s', conn_id %d, " + \
            "type '%s' xid: %d, command: %s",
            displayname, aconn.conn_id, agent.agent_type,
            req.xid, safecmd(cli_command))
        try:
            aconn.httpconn.request('POST', '/cli', req.send_body, headers)
            self.log.debug('sent cli command.')

            res = aconn.httpconn.getresponse()

            self.log.debug('_send_cli: command: cli: ' + \
                           str(res.status) + ' ' + str(res.reason))
            # print "headers:", res.getheaders()
            self.log.debug("_send_cli reading...")
            body_json = res.read()

            if res.status != httplib.OK:
                self.log.error("_send_cli: command: '%s', %d %s : %s",
                               safecmd(cli_command), res.status,
                               res.reason, body_json)
                reason = "Command sent to agent failed. Error: " + res.reason
                self.remove_agent(agent, reason)
                return self.httperror(res, method="POST",
                                      displayname=agent.displayname,
                                      uri=uri, body=body_json)

        except (httplib.HTTPException, EnvironmentError) as ex:
            self.log.error(\
                "_send_cli: command '%s' failed with httplib.HTTPException: %s",
                           safecmd(cli_command), str(ex))
            self.remove_agent(agent, EventControl.AGENT_COMM_LOST) # bad agent
            return self.error("_send_cli: '%s' command failed with: %s" %
                              (safecmd(cli_command), str(ex)))
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
            return self.error("POST /cli xid expected: %d but was %d" % \
                              (req.xid, body['xid']), body)

        if not body.has_key('run-status'):
            return self.error("POST /cli response missing 'run-status'", body)
        if body['run-status'] != 'running' and body['run-status'] != 'finished':
            # FIXME: could possibly be finished.
            return self.error(\
                "POST /cli response for 'run-status' was not 'running'", body)

        return body

    def _send_cleanup(self, xid, agent, orig_cli_command):
        """Send a "cleanup" command to an Agent.
            On success, returns the body of the reply.
            On failure, throws an exception.

            orig_cli_command is used only for debugging/printing.

            Called without the connection lock."""

        self.log.debug("_send_cleanup")
        aconn = agent.connection
        aconn.lock()
        self.log.debug("_send_cleanup got lock")

        req = CleanupRequest(xid)
        headers = {"Content-Type": "application/json"}
        uri = self.CLI_URI

        self.log.debug('about to send the cleanup command, xid %d', xid)
        try:
            aconn.httpconn.request('POST', uri, req.send_body, headers)
            self.log.debug('sent cleanup command')
            res = aconn.httpconn.getresponse()
            self.log.debug('command: cleanup: ' + \
                               str(res.status) + ' ' + str(res.reason))
            body_json = res.read()
            if res.status != httplib.OK:
                self.log.error("_send_cleanup: POST %s for cmd '%s' failed,"
                               "%d %s : %s", uri, orig_cli_command,
                               res.status, res.reason, body_json)
                alert = "Agent command failed with status: " + str(res.status)
                self.remove_agent(agent, alert)
                return self.httperror(res, method="POST",
                                      displayname=agent.displayname,
                                      uri=uri, body=body_json)

            self.log.debug("headers: " + str(res.getheaders()))
            self.log.debug("_send_cleanup reading...")

        except (httplib.HTTPException, EnvironmentError) as ex:
            # bad agent
            self.log.error("_send_cleanup: POST %s for '%s' failed with: %s",
                           uri, orig_cli_command, str(ex))
            self.remove_agent(agent, "Command to agent failed. " \
                                  + "Error: " + str(ex))
            return self.error("'%s' failed for command '%s' with: %s" % \
                                  (uri, orig_cli_command, str(ex)), {})
        finally:
            # Must call aconn.unlock() even after self.remove_agent(),
            # since another thread may waiting on the lock.
            aconn.unlock()
            self.log.debug("_send_cleanup unlocked")

        self.log.debug("done reading.")
        body = json.loads(body_json)
        if body == None:
            return self.error("POST /%s getresponse returned null body" % uri,
                              return_dict={})
        return body

    def copy_cmd(self, source_agentid, source_path, target_agentid, target_dir):
        """Sends a phttp command and checks the status.
           copy from  source_agentid /path/to/file target_agentid target-dir
                                      <source_path>            <target-dir>
           generates:
               phttp.exe GET https://primary-ip:192.168.1.1/file dir/
           and sends it as a cli command to agent:
                target-agentid
           Returns the body dictionary from the status.
        """
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals

        if not len(source_path):
            return self.error("[ERROR] Invalid source path with no length.")

        agents = self.agentmanager.all_agents()
        src = dst = None

        for key in agents.keys():
            self.agentmanager.lock()
            if not agents.has_key(key):
                self.log.info(
                    "copy_cmd: agent with conn_id %d is now " + \
                    "gone and won't be checked.", key)
                self.agentmanager.unlock()
                continue
            agent = agents[key]
            self.agentmanager.unlock()

            if agent.agentid == source_agentid:
                src = agent
            if agent.agentid == target_agentid:
                dst = agent

        msg = ""
        # fixme: make sure the source isn't the same as the target
        if not src:
            msg = "No connected source agent with agentid: %d." % \
              source_agentid
        if not dst:
            msg += "No connected target agent with agentid: %s." % \
              target_agentid

        if not src or not dst:
            return self.error(msg)

        if src.iswin:
            # Enable the firewall port on the source host.
            self.log.debug("Enabling firewall port %d on src host '%s'", \
                                    src.listen_port, src.displayname)
            fw_body = src.firewall.enable([src.listen_port])
            if fw_body.has_key("error"):
                self.log.error(\
                    "firewall enable port %d on src host %s failed with: %s",
                        src.listen_port, src.displayname, fw_body['error'])
                data = agent.todict()
                data['error'] = fw_body['error']
                data['info'] = "Port " + str(src.listen_port)
                self.event_control.gen(EventControl.FIREWALL_OPEN_FAILED, data)
                return fw_body

        source_ip = src.ip_address

       # Make sure the target directory on the target agent exists.
        try:
            dst.filemanager.mkdirs(target_dir)
        except (IOError, ValueError):
            self.log.error(\
                "copycmd: Could not create directory: '%s'" % target_dir)
            return self.error(\
                "Could not create directory '%s' on target agent '%s'" % \
                target_dir, dst.displayname)

        if src.iswin:
            command = 'phttp GET "https://%s:%s/%s" "%s"' % \
                (source_ip, src.listen_port, source_path, target_dir)
        else:
            command = 'phttp GET "https://%s:%s%s" "%s"' % \
                (source_ip, src.listen_port, source_path, target_dir)

        try:
            entry = meta.Session.query(Agent).\
                filter(Agent.agentid == src.agentid).\
                one()
        except sqlalchemy.orm.exc.NoResultFound:
            self.log.error("Source agent not found!  agentid: %d", src.agentid)
            return self.error("Source agent not found in agent table: %d " % \
                                                                src.agentid)

        env = {u'BASIC_USERNAME': entry.username,
               u'BASIC_PASSWORD': entry.password}

        self.log.debug("agent username: %s, password: %s", entry.username,
                                                            entry.password)
        # Send command to target agent
        copy_body = self.cli_cmd(command, dst, env=env)
        return copy_body

    def restore_cmd(self, agent, backup_full_path, orig_state,
                    no_config=False, userid=None):
        # pylint: disable=too-many-arguments
        """Do a tabadmin restore for the backup_full_path.
           The backup_full_path may be in cloud storage, or a volume
           on some agent.

           The "agent" argument must be the primary agent.

           Returns a body with the results/status.
        """
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements

        # If the backup file is not on the primary agent,
        # from to a staging area on the primary from:
        #   1) another agent
        # or
        #   2) cloud storage
        try:
            got = GetFile(self, agent, backup_full_path)
        except IOError as ex:
            self.state_manager.update(orig_state)
            return self.error("restore_cmd failure: %s" % str(ex))

        # The restore file is now on the Primary Agent.
        data = agent.todict()
        self.event_control.gen(EventControl.RESTORE_STARTED,
                               data, userid=userid)

        reported_status = self.statusmon.get_reported_status()

        if reported_status == TableauProcess.STATUS_RUNNING:
            # Restore can run only when tableau is stopped.
            self.state_manager.update(StateManager.STATE_STOPPING_RESTORE)
            self.log.debug("----------Stopping Tableau for restore-----------")
            stop_body = self.cli_cmd("tabadmin stop", agent)
            if stop_body.has_key('error'):
                self.log.info("Restore: tabadmin stop failed")
                if got.copied:
                    # If the file was copied to the Primary, delete
                    # the temporary backup file we copied to the Primary.
                    self.delete_vol_file(agent, got.primary_full_path)
                self.state_manager.update(orig_state)
                return stop_body

            self.event_control.gen(EventControl.STATE_STOPPED, data,
                                   userid=userid)

        # 'tabadmin restore ...' starts tableau as part of the
        # restore procedure.
        # fixme: Maybe the maintenance web server wasn't running?
        # We currently don't keep track, but assume the maintenance
        # web server may be running if Tableau is stopped.
        maint_msg = ""
        if orig_state == StateManager.STATE_STOPPED:
            maint_body = self.maint("stop", agent=agent)
            if maint_body.has_key("error"):
                self.log.info(
                        "Restore: maint stop failed: " + maint_body['error'])
                # continue on, not a fatal error...
                maint_msg = "Restore: maint stop failed.  Error was: %s" \
                                                    % maint_body['error']

        self.state_manager.update(StateManager.STATE_STARTING_RESTORE)

        cmd = 'tabadmin restore \\\"%s\\\"' % got.primary_full_path
        if no_config:
            cmd += ' --no-config'

        try:
            self.log.debug("restore sending command: %s", cmd)
            restore_body = self.cli_cmd(cmd, agent)
        except httplib.HTTPException, ex:
            restore_body = {"error": "HTTP Exception: " + str(ex)}

        if restore_body.has_key('error'):
            restore_success = False
        else:
            restore_success = True

        if maint_msg != "":
            info = maint_msg
        else:
            info = ""

        # fixme: Do we need to add restore information to the database?
        # fixme: check status before cleanup? Or cleanup anyway?

        if got.copied:
            # If the file was copied to the Primary, delete
            # the temporary backup file we copied to the Primary.
            delete_body = self.delete_vol_file(agent,
                                                 got.primary_full_path)
            if 'error' in delete_body:
                info += '\n' + delete_body['error']

        if restore_success:
            self.state_manager.update(StateManager.STATE_STARTED)
            self.event_control.gen(EventControl.STATE_STARTED, data,
                                   userid=userid)
        else:
            # On a successful restore, tableau starts itself.
            # fixme: eventually control when tableau is started and
            # stopped, rather than have tableau automatically start
            # during the restore.  (Tableau does not support this currently.)
            self.log.info("Restore: starting tableau after failed restore.")
            start_body = self.cli_cmd("tabadmin start", agent)
            if 'error' in start_body:
                self.log.info(\
                    "Restore: 'tabadmin start' failed after failed restore.")
                msg = "Restore: 'tabadmin start' failed after failed restore."
                msg += " Error was: %s" % start_body['error']
                info += "\n" + msg

                 # The "tableau start" failed.  Go back to the "STOPPED" state.
                self.state_manager.update(StateManager.STATE_STOPPED)
            else:
                # The "tableau start" succeeded
                self.state_manager.update(StateManager.STATE_STARTED)
                self.event_control.gen(EventControl.STATE_STARTED, data,
                                       userid=userid)

        if info:
            restore_body['info'] = info.strip()

        return restore_body

    # FIXME: use filemanager.delete() instead?
    def delete_vol_file(self, agent, source_fullpathname):
        """Delete a file, check the error, and return the body result."""
        self.log.debug("Removing file '%s'", source_fullpathname)
        cmd = 'CMD /C DEL \\\"%s\\\"' % source_fullpathname
        remove_body = self.cli_cmd(cmd, agent)
        if remove_body.has_key('error'):
            self.log.info('DEL of "%s" failed.', source_fullpathname)
            # fixme: report somewhere the DEL failed.
        return remove_body


    # FIXME: move to CloudManager
    def delete_cloud_file(self, file_entry):
        cloud_entry = self.cloud.get_by_cloudid(file_entry.storageid)
        if not cloud_entry:
            raise IOError("No such cloudid: %d for file %s" % \
                          (file_entry.cloudid, file_entry.name))

        if cloud_entry.cloud_type == CloudManager.CLOUD_TYPE_S3:
            self.cloud.s3.delete_file(cloud_entry, file_entry.name)
        elif cloud_entry.cloud_type == CloudManager.CLOUD_TYPE_GCS:
            self.cloud.gcs.delete_file(cloud_entry, file_entry.name)
        else:
            msg = "delete_cloud_file: Unknown cloud_type %s for file: %s" % \
                  (cloud_entry.cloud_type, file_entry.name)
            self.log.error(msg)
            raise IOError(msg)
        try:
            self.files.remove(file_entry.storageid)
        except sqlalchemy.orm.exc.NoResultFound:
            return {'error': ("fileid %d not found: name=%s storageid=%d" % \
                    (file_entry.storageid, file_entry.name,
                    file_entry.storageid))}

    def move_bucket_subdirs_to_path(self, in_bucket, in_path):
        """ Given:
                in_bucket: palette-storage/subdir/dir2
                in_path:   filename
            return:
                bucket:    palette-storage
                path:      subdir/dir2/filename
        """

        if in_bucket.find('/') != -1:
            bucket, rest = in_bucket.split('/', 1)
            path = os.path.join(rest, in_path)
        elif in_bucket.find('\\') != -1:
            bucket, rest = in_bucket.split('\\', 1)
            path = ntpath.join(rest, in_path)
        else:
            bucket = in_bucket
            path = in_path
        return (bucket, path)

    def _get_cli_status(self, xid, agent, orig_cli_command):
        """Gets status on the command and xid.  Returns:
            Body in json with status/results.

            orig_cli_command is used only for debugging/printing.

            Note: Do not call this with the agent lock since
            we keep requesting status until the command is
            finished and that could be a long time.
        """
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-return-statements

#        debug for testing agent disconnects
#        print "sleeping"
#        time.sleep(5)
#        print "awake"

        uri = self.CLI_URI + "?xid=" + str(xid)
        headers = {"Content-Type": "application/json"}

        aconn = agent.connection
        while True:
            self.log.debug(
                "about to get status of cli command '%s', xid %d, conn_id %d",
                           safecmd(orig_cli_command), xid, aconn.conn_id)

            # If the agent is initializing, then "agent_connected"
            # will not know about it yet.
            if not aconn.initting and \
                    not self.agentmanager.agent_connected(aconn):
                self.log.warning(
                    "Agent '%s' (type: '%s', uuid %s, conn_id %d) " + \
                    "disconnected before finishing: %s",
                     agent.displayname, agent.agent_type, agent.uuid,
                     aconn.conn_id, uri)
                return self.error(("Agent '%s' (type: '%s', uuid %s, " + \
                    "conn_id %d), disconnected before finishing: %s") %
                    (agent.displayname, agent.agent_type, agent.uuid,
                    aconn.conn_id, uri))

            aconn.lock()
            self.log.debug("Sending GET " + uri)

            try:
                aconn.httpconn.request("GET", uri, None, headers)

                self.log.debug("Getting response from GET " +  uri)
                res = aconn.httpconn.getresponse()
                self.log.debug("status: " + str(res.status) + ' ' + \
                                                            str(res.reason))
                if res.status != httplib.OK:
                    self.remove_agent(agent,
                                 EventControl.AGENT_RETURNED_INVALID_STATUS)
                    return self.httperror(res,
                                          displayname=agent.displayname,
                                          uri=uri)

#                debug for testing agent disconnects
#                print "sleeping"
#                time.sleep(5)
#                print "awake"

                self.log.debug("_get_status reading.")
                body_json = res.read()
                aconn.unlock()

                body = json.loads(body_json)
                if body == None:
                    return self.error(\
                            "Get /%s getresponse returned a null body" % uri)

                self.log.debug("body = " + str(body))
                if not body.has_key('run-status'):
                    self.remove_agent(agent,
                                     EventControl.AGENT_RETURNED_INVALID_STATUS)
                    return self.error(\
                        "GET %s command reply was missing 'run-status'!  " + \
                        "Will not retry." % (uri), body)

                if body['run-status'] == 'finished':
                    # Make sure if the command failed, that the 'error'
                    # key is set.
                    if body['exit-status'] != 0:
                        if body.has_key('stderr') and body['stderr']:
                            body['error'] = body['stderr']
                        else:
                            body['error'] = u"Failed with exit status: %d" % \
                                                            body['exit-status']
                    return body
                elif body['run-status'] == 'running':
                    time.sleep(self.cli_get_status_interval)
                    continue
                else:
                    self.remove_agent(agent,
                        "Communication failure with agent:  " + \
                        "Unknown run-status returned from agent: %s" % \
                                            body['run-status'])    # bad agent
                    return self.error("Unknown run-status: %s.  Will not " + \
                                            "retry." % body['run-status'], body)
            except httplib.HTTPException, ex:
                self.remove_agent(agent,
                            "HTTP communication failure with agent: " + str(ex))
                return self.error("GET %s failed with HTTPException: %s" % \
                                  (uri, str(ex)))
            except EnvironmentError, ex:
                self.remove_agent(agent, "Communication failure with " + \
                                  "agent. Unexpected error: " + str(ex))
                return self.error("GET %s failed with: %s" % (uri, str(ex)))

    def odbc_ok(self):
        """Reports back True if odbc commands can be run now to
           the postgres database.  odbc commands should be not sent
           in these cases:
            * When the tableau is stopped, since the postgres is also
              stopped when tableau is stopped.
            * When in "UPGRADE" mode.
        """
        main_state = self.state_manager.get_state()
        if main_state in (StateManager.STATE_STARTED,
                                            StateManager.STATE_DEGRADED):
            return True
        else:
            return False

    def active_directory_verify(self, agent, windomain, username, password):
        data = {'domain': windomain, 'username':username, 'password':password}
        body = agent.connection.http_send_json('/ad', data)
        return json.loads(body)

    def upgrading(self):
        main_state = self.state_manager.get_state()
        if main_state == StateManager.STATE_UPGRADING:
            return True
        else:
            return False

    def get_pinfo(self, agent, update_agent=False):
        if self.upgrading():
            self.log.info("get_pinfo: Failing due to UPGRADING")
            raise exc.InvalidStateError("Cannot run command while UPGRADING")

        body = self.cli_cmd('pinfo', agent, immediate=True)
        # FIXME: add a function to test cli success (cli_success?)
        if not 'exit-status' in body:
            raise IOError("Missing 'exit-status' from pinfo command response.")
        if body['exit-status'] != 0:
            raise IOError("pinfo failed with exit status: %d" % \
                                                            body['exit-status'])
        json_str = body['stdout']
        try:
            pinfo = json.loads(json_str)
        except ValueError, ex:
            self.log.error("Bad json from pinfo. Error: %s, json: %s", \
                           str(ex), json_str)
            raise IOError("Bad json from pinfo.  Error: %s, json: %s" % \
                          (str(ex), json_str))
        if pinfo is None:
            self.log.error("Bad pinfo output: %s", json_str)
            raise IOError("Bad pinfo output: %s" % json_str)

        # When we are called from init_new_agent(), we don't know
        # the agent_type yet and update_agent_pinfo_vols() needs to
        # know the agent type for the volume table values.
        # When we are called by do_info() we will know the agent type.
        if update_agent:
            if agent.agent_type:
                self.agentmanager.update_agent_pinfo_dirs(agent, pinfo)
                self.agentmanager.update_agent_pinfo_vols(agent, pinfo)
            else:
                self.log.error(\
                    "get_pinfo: Could not update agent: unknown " + \
                                    "displayname.  uuid: %s", agent.uuid)
                raise IOError("get_pinfo: Could not update agent: unknown " + \
                        "displayname.  uuid: %s" % agent.uuid)

        return pinfo

    def yml(self, agent, set_agent_types=True):
        path = agent.path.join(agent.tableau_data_dir, "data", "tabsvc",
                               "config", "workgroup.yml")
        yml_contents = agent.filemanager.get(path)
        body = AgentYmlEntry.sync(self.environment.envid, yml_contents)

        if set_agent_types:
            # See if any worker agents need to be reclassified as
            # archive agents or vice versa.
            self.agentmanager.set_all_agent_types()

        return body

    def sync_cmd(self, agent, check_odbc_state=True):
        """sync/copy tables from tableau to here."""

        if check_odbc_state and not self.odbc_ok():
            main_state = self.state_manager.get_state()
            self.log.info("Failed.  Current state: %s", main_state)
            raise exc.InvalidStateError(
                "Cannot run command while in state: %s" % main_state)

        error_msg = ""
        sync_dict = {}

        body = Site.sync(agent)
        if 'error' in body:
            error_msg += "Site sync failure: " + body['error']
        else:
            sync_dict['sites'] = body['count']

        body = Project.sync(agent)
        if 'error' in body:
            if error_msg:
                error_msg += ", "
            error_msg += "Project sync failure: " + body['error']
        else:
            sync_dict['projects'] = body['count']

        body = DataConnection.sync(agent)
        if 'error' in body:
            if error_msg:
                error_msg += ", "
            error_msg += "DataConnection sync failure: " + body['error']
        else:
            sync_dict['data-connections'] = body['count']

        if error_msg:
            sync_dict['error'] = error_msg

        return sync_dict

    def maint(self, action, agent=None, send_alert=True):
        if action not in ("start", "stop"):
            self.log.error("Invalid maint action: %s", action)
            return self.error("Bad maint action: %s" % action)

        manager = self.agentmanager

        # FIXME: Tie agent to domain
        if not agent:
            agent = manager.agent_by_type(AgentManager.AGENT_TYPE_PRIMARY)
            if not agent:
                return self.error(
                            "maint: no primary agent is known and enabled.")

            elif not agent.connection:
                return self.error("maint: no primary agent is connected.")

        send_maint_body = self.set_maint_body(action)

        body = self.send_immediate(agent, "POST", "/maint", send_maint_body)

        if body.has_key("error"):
            data = agent.todict()
            data['error'] = body['error']
            if action == "start":
                self.event_control.gen(EventControl.MAINT_START_FAILED, data)
            else:
                self.event_control.gen(EventControl.MAINT_STOP_FAILED, data)
            return body

        if not send_alert:
            return body

        if action == 'start':
            self.event_control.gen(EventControl.MAINT_ONLINE, agent.todict())
        else:
            self.event_control.gen(EventControl.MAINT_OFFLINE, agent.todict())

        return body

    def set_maint_body(self, action):
        envid = self.environment.envid
        send_body = {"action": action}

        gateway_ports = AgentYmlEntry.get(envid, 'gateway.ports', default=None)
        if gateway_ports:
            ports = gateway_ports.split(';')
            try:
                listen_port = int(ports[0])
                send_body["listen-port"] = listen_port
            except StandardError:
                self.log.error("Invalid yml entry for 'gatway.ports': %s",
                                gateway_ports)

        ssl_port = AgentYmlEntry.get(envid, 'ssl.listen.port', default=None)
        if ssl_port:
            try:
                ssl_port = int(ssl_port)
                send_body['ssl-listen-port'] = ssl_port
            except StandardError:
                self.log.error("Invalid yml entry for 'ssl.listen.port': %s",
                                ssl_port)

        # Mapping from the yml file to the json to send.
        file_map = {'ssl.cert.file': 'ssl-cert-file',
                    'ssl.key.file': 'ssl-cert-key-file',
                    'ssl.chain.file': 'ssl-cert-chain-file'}

        for key in file_map.keys():
            value = AgentYmlEntry.get(envid, key, default=None)
            if not value:
                continue

            send_body[file_map[key]] = value

        return send_body

    def archive(self, agent, action, port=-1):
        send_body = {"action": action}
        if port > 0:
            send_body["port"] = port

        return self.send_immediate(agent, "POST", "/archive", send_body)

    def ping(self, agent):

        return self.send_immediate(agent, "POST", "/ping")

    def send_immediate(self, agent, method, uri, send_body=""):
        """Sends the request specified by:
                agent:      agent to send to.
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

        aconn = agent.connection

        self.log.debug(
            "about to send an immediate command to '%s', conn_id %d, " + \
                "type '%s', method '%s', uri '%s', body '%s'",
                    agent.displayname, aconn.conn_id, agent.agent_type,
                    method, uri, send_body)

        aconn.lock()
        body = {}
        try:
            aconn.httpconn.request(method, uri, send_body, headers)
            res = aconn.httpconn.getresponse()

            rawbody = res.read()
            if res.status != httplib.OK:
                # bad agent
                self.log.error(\
                    "immediate command to %s failed with status %d: %s " + \
                    "%s, body: %s:",
                            agent.displayname, res.status, method, uri, rawbody)
                self.remove_agent(agent,\
                    ("Communication failure with agent. " +\
                    "Immediate command to %s, status returned: " +\
                    "%d: %s %s, body: %s") % \
                        (agent.displayname, res.status, method, uri, rawbody))
                return self.httperror(res, method=method,
                                      displayname=agent.displayname,
                                      uri=uri, body=rawbody)
            elif rawbody:
                body = json.loads(rawbody)
            else:
                body = {}
        except (httplib.HTTPException, EnvironmentError) as ex:
            self.log.error("Agent send_immediate command %s %s failed: %s",
                           method, uri, str(ex))
            self.remove_agent(agent, \
                    "Agent send_immediate command %s %s failed: %s" % \
                              (method, uri, str(ex)))
            return self.error("send_immediate method %s, uri %s failed: %s" % \
                              (method, uri, str(ex)))
        finally:
            aconn.unlock()

        self.log.debug(
            "send immediate %s %s success, conn_id %d, response: %s",
                                    method, uri, aconn.conn_id, str(body))
        return body

    def displayname_cmd(self, aconn, uuid, displayname):
        """Sets displayname for the agent with the given hostname. At
           this point assumes uuid is unique in the database."""

        self.agentmanager.set_displayname(aconn, uuid, displayname)

    def ziplogs_cmd(self, agent, userid=None):
        """Run tabadmin ziplogs."""
        # pylint: disable=too-many-locals

        if userid == None:
            auto = True     # It is an 'automatic/scheduled' backup
        else:
            auto = False    # It was requested by a specific user

        # fixme: get more accurate estimate of ziplog size
        min_disk_needed = agent.tableau_data_size * .3
        # Disk space check.
        try:
            dcheck = DiskCheck(self, agent, self.LOG_DIR,
                               FileManager.FILE_TYPE_ZIPLOG, min_disk_needed)
        except DiskException, ex:
            self.log.error("ziplogs_cmd: %s", str(ex))
            return self.error("ziplogs_cmd: %s" % str(ex))

        data = agent.todict()
        self.event_control.gen(EventControl.ZIPLOGS_STARTED,
                               data, userid=userid)

        ziplogs_name = time.strftime(self.FILENAME_FMT) + ".logs.zip"
        ziplogs_full_path = agent.path.join(dcheck.primary_dir, ziplogs_name)
        cmd = 'tabadmin ziplogs -f -l -n -a \\\"%s\\\"' % ziplogs_full_path
        body = self.cli_cmd(cmd, agent)
        body[u'info'] = unicode(cmd)

        if success(body):
            ziplog_size_body = agent.filemanager.filesize(ziplogs_full_path)
            if not success(ziplog_size_body):
                self.log.error("Failed to get size of ziplogs file %s: %s",
                               ziplogs_full_path, ziplog_size_body['error'])
                ziplog_size = 0
            else:
                ziplog_size = ziplog_size_body['size']

            # Place the file where it belongs (different agent, cloud, etc.)
            place = PlaceFile(self, agent, dcheck, ziplogs_full_path,
                              ziplog_size, auto)
            body['info'] += '\n' + place.info

            rotate_info = self.rotate_ziplogs()
            body['info'] += rotate_info

        if 'error' in body:
            self.event_control.gen(EventControl.ZIPLOGS_FAILED,
                                   dict(body.items() + data.items()))
        else:
            self.event_control.gen(EventControl.ZIPLOGS_FINISHED,
                                   dict(body.items() + data.items()))
        return body

    def cleanup_cmd(self, agent, userid=None):
        """Run tabadmin cleanup'."""

        data = agent.todict()
        self.event_control.gen(EventControl.CLEANUP_STARTED, data,
                               userid=userid)
        body = self.cli_cmd('tabadmin cleanup', agent)
        if 'error' in body:
            self.event_control.gen(EventControl.CLEANUP_FAILED,
                                   dict(body.items() + data.items()),
                                   userid=userid)
        else:
            self.event_control.gen(EventControl.CLEANUP_FINISHED,
                                   dict(body.items() + data.items()),
                                   userid=userid)
        return body

    # FIXME: allow this to take *args
    def error(self, msg, return_dict=None):
        """Returns error dictionary in standard format.  If passed
           a return_dict, then adds to it, otherwise a new return_dict
           is created."""
        if return_dict is None:
            return_dict = {}
        return_dict['error'] = unicode(msg)
        return return_dict

    def controller_init_events(self):
        """Generate an event if we are running a new version."""
        current_version = version()
        last_version = self.system.get(SystemConfig.PALETTE_VERSION,
                                       default=None)

        body = {'version_previous': last_version,
                'version_current': current_version}

        self.event_control.gen(EventControl.CONTROLLER_STARTED, body)

        if current_version == last_version:
            return

        self.system.save(SystemConfig.PALETTE_VERSION, current_version)

        self.event_control.gen(EventControl.PALETTE_UPDATED, body)

    def httperror(self, res, error='HTTP failure',
                  displayname=None, method='GET', uri=None, body=None):
        """Returns a dict representing a non-OK HTTP response."""
        # pylint: disable=too-many-arguments
        if body is None:
            body = res.read()
        data = {
            'error': error,
            'status-code': res.status,
            'reason-phrase': res.reason,
            }
        if method:
            data['method'] = method
        if uri:
            data['uri'] = uri
        if body:
            data['body'] = body
        if displayname:
            data['agent'] = displayname
        return data

    def init_new_agent(self, agent):
        """Agent-related configuration on agent connect.
            Args:
                aconn: agent connection
            Returns:
                pinfo dictionary:  The agent responded correctly.
                False:  The agent responded incorrectly.
        """

        tableau_install_dir = "tableau-install-dir"
        aconn = agent.connection

        pinfo = self.get_pinfo(agent, update_agent=False)

        self.log.debug("info returned from %s: %s",
                       aconn.displayname, str(pinfo))
        # Set the type of THIS agent.
        if tableau_install_dir in pinfo:
            # FIXME: don't duplicate the data
            agent.agent_type = aconn.agent_type \
                = AgentManager.AGENT_TYPE_PRIMARY

            if pinfo[tableau_install_dir].find(':') == -1:
                self.log.error("agent %s is missing ':': %s for %s",
                               aconn.displayname, tableau_install_dir,
                               agent.tableau_install_dir)
                return False
        else:
            if self.agentmanager.is_tableau_worker(agent):
                agent.agent_type = aconn.agent_type = \
                                    AgentManager.AGENT_TYPE_WORKER
            else:
                agent.agent_type = aconn.agent_type = \
                                    AgentManager.AGENT_TYPE_ARCHIVE

        if agent.iswin:
            self.firewall_manager.do_firewall_ports(agent)

        self.clean_xid_dirs(agent)
        self.config_servers(agent)

        # This saves directory-related info from pinfo: it
        # does not save the volume info since we may not
        # know the displayname yet and the displayname is
        # needed for a disk-usage event report.
        self.agentmanager.update_agent_pinfo_dirs(agent, pinfo)

        # Note: Don't call this before update_agent_pinfo_dirs()
        # (needed for agent.tableau_data_dir).
        if agent.agent_type == AgentManager.AGENT_TYPE_PRIMARY:
            self.yml(agent, set_agent_types=False) # raises an exception on fail
            if not self.upgrading():
                # These can all fail as long as they don't get an IOError.
                # For example, if tableau is stopped, these will fail,
                # but we don't know tableau's status yet and it's
                # worth trying, especially to import the users.
                if success(self.auth.load(agent, check_odbc_state=False)):
                    self.sync_cmd(agent, check_odbc_state=False)
                    self.extract.load(agent, check_odbc_state=False)
                else:
                    self.log.debug(
                        "init_new_agent: Couldn't do initial import of " + \
                        "auth, etc. probably due to tableau stopped.")

        return pinfo

    def clean_xid_dirs(self, agent):
        """Remove old XID directories."""
        xid_dir = agent.path.join(agent.data_dir, "XID")
        body = agent.filemanager.listdir(xid_dir)

        if not success(body):
            self.log.error("Could not list the XID directory '%s': %s",
                           xid_dir, body['error'])
            return

        if not 'directories' in body:
            self.log.error(
                           ("clean_xid_dirs: Filemanager response missing " + \
                             "directories.  Response: %s") % str(body))
            return

        for rem_dir in body['directories']:
            full_path = agent.path.join(xid_dir, rem_dir)
            self.log.debug("Removing %s", full_path)
            agent.filemanager.delete(full_path)

    def config_servers(self, agent):
        """Configure the maintenance and archive servers."""
        if agent.agent_type == AgentManager.AGENT_TYPE_PRIMARY:
            # Put into a known state
            body = self.maint("stop", agent=agent, send_alert=False)
            if body.has_key("error"):
                data = agent.todict()
                self.event_control.gen(EventControl.MAINT_STOP_FAILED,
                                       dict(body.items() + data.items()))

        body = self.archive(agent, "stop")
        if body.has_key("error"):
            self.event_control.gen(EventControl.ARCHIVE_STOP_FAILED,
                                   dict(body.items() + agent.todict().items()))
        # Get ready.
        body = self.archive(agent, "start")
        if body.has_key("error"):
            self.event_control.gen(EventControl.ARCHIVE_START_FAILED,
                                   dict(body.items() + agent.todict().items()))

        # If tableau is stopped, turn on the maintenance server
        if agent.agent_type != AgentManager.AGENT_TYPE_PRIMARY:
            return

    def remove_agent(self, agent, reason="", gen_event=True):
        manager = self.agentmanager
        manager.remove_agent(agent, reason=reason, gen_event=gen_event)
        # FIXME: At the least, we need to add the domain to the check
        #        for a primary; better, however, would be to store the
        #        uuid of the status with the status and riff off uuid.
        if not manager.agent_conn_by_type(AgentManager.AGENT_TYPE_PRIMARY):
            session = meta.Session()
            self.statusmon.remove_all_status()
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
        self.flush()

    def flush(self):
        self.writeln(self.buf)
        self.buf = ''

def main():
    # pylint: disable=too-many-statements,too-many-locals
    # pylint: disable=attribute-defined-outside-init

    import argparse
    import logger

    parser = argparse.ArgumentParser(description='Palette Controller')
    parser.add_argument('config', nargs='?', default=None)
    parser.add_argument('--nostatus', action='store_true', default=False)
    parser.add_argument('--noping', action='store_true', default=False)
    parser.add_argument('--nosched', action='store_true', default=False)
    args = parser.parse_args()

    config = Config(args.config)
    host = config.get('controller', 'host', default='localhost')
    port = config.getint('controller', 'port', default=9000)
    agent_port = config.getint('controller', 'agent_port', default=22)

    # loglevel is entirely controlled by the INI file.
    logger.make_loggers(config)
    log = logger.get(Controller.LOGGER_NAME)
    log.info("Controller version: %s", version())

    # Log stderr to the log file too.
    # NOTE: stdout is not logged so that PDB will work.
    sys.stderr = StreamLogger(log, tag='STD')

    # database configuration
    url = config.get("database", "url")
    echo = config.getboolean("database", "echo", default=False)
    max_overflow = config.getint("database", "max_overflow", default=10)

    # engine is once per single application process.
    # see http://docs.sqlalchemy.org/en/rel_0_9/core/connections.html
    meta.engine = sqlalchemy.create_engine(url, echo=echo,
                                           max_overflow=max_overflow)
    # Create the table definition ONCE, before all the other threads start.
    meta.Base.metadata.create_all(bind=meta.engine)
    meta.Session = scoped_session(sessionmaker(bind=meta.engine,
                                   autoflush=False, expire_on_commit=False))

    log.debug("Starting agent listener.")

    server = Controller((host, port), CliHandler)
    server.config = config
    server.log = log
    server.cli_get_status_interval = \
      config.getint('controller', 'cli_get_status_interval', default=10)
    server.noping = args.noping
    server.event_debug = config.getboolean('default',
                                           'event_debug',
                                           default=False)
    Domain.populate()
    domainname = config.get('palette', 'domainname')
    server.domain = Domain.get_by_name(domainname)
    Environment.populate()
    server.environment = Environment.get()

    server.system = SystemManager(server)
    SystemManager.populate()

    StateControl.populate()

    DataSourceTypes.populate()

    server.auth = AuthManager(server)
    server.cred = CredentialManager(server)
    server.extract = ExtractManager(server)
    server.hrman = HttpRequestManager(server)

    Role.populate()
    UserProfile.populate()

    # Must be done after auth, since it uses the users table.
    server.alert_email = AlertEmail(server)

    EventControl.populate()
    server.event_control = EventControlManager(server)

    # Send controller started and potentially "new version" events.
    server.controller_init_events()

    server.workbooks = WorkbookManager(server)
    server.files = FileManager(server)
    server.cloud = CloudManager(server)
    server.firewall_manager = FirewallManager(server)
    server.license_manager = LicenseManager(server)
    server.state_manager = StateManager(server)

    server.ports = PortManager(server)
    server.ports.populate()

    manager = AgentManager(server, port=agent_port)
    server.agentmanager = manager

    manager.update_last_disconnect_time()
    manager.start()

    # Need to instantiate to initialize state and status tables,
    # even if we don't run the status thread.
    statusmon = TableauStatusMonitor(server, manager)
    server.statusmon = statusmon

    if not args.nosched:
        server.sched = Sched(server)
        server.sched.populate()

    if not args.nostatus:
        log.debug("Starting status monitor.")
        statusmon.start()

    server.serve_forever()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print "\nInterrupted.  Exiting."
        # pylint: disable=protected-access
        os._exit(1)
