""" The main server instance of the controller. """
import logging
import sys
import os
import SocketServer as socketserver

import json
import time
import datetime

import exc

import httplib
import ntpath
import urllib
from rwlock import RWLock
from urlparse import urlsplit

import sqlalchemy
import akiri.framework.sqlalchemy as meta

# These are need for create_all().
# FIXME: these should logically go in __init__.py.
# pylint: disable=unused-import
from agentmanager import AgentManager
from agent import Agent, AgentVolumesEntry
from alert_email import AlertEmail
from alert_setting import AlertSetting
from auth import AuthManager
from cli_cmd import CliCmd
from cloud import CloudEntry
from config import Config
from passwd import aes_encrypt
from credential import CredentialEntry, CredentialManager
from diskcheck import DiskCheck, DiskException
from datasources import DataSourceManager
from data_source_types import DataSourceTypes
from domain import Domain
from environment import Environment
from event_control import EventControl, EventControlManager
from extracts import ExtractManager
from extract_archive import ExtractRefreshManager
from files import FileManager
from firewall_manager import FirewallManager
from http_control import HttpControl
from http_requests import HttpRequestEntry, HttpRequestManager
from licensing import LicenseManager, LicenseEntry
from metrics import MetricManager
from notifications import NotificationManager
#from package import Package
from ports import PortManager
from profile import UserProfile, Role
from sched import Sched, Crontab
from state import StateManager
from state_control import StateControl
from system import SystemManager, SystemKeys
from tableau import TableauStatusMonitor, TableauProcess
from workbooks import WorkbookEntry, WorkbookUpdateEntry, WorkbookManager
from yml import YmlEntry, YmlManager

# pylint seems to get this wrong...
from support import support_case

#pylint: enable=unused-import

from sites import Site
from projects import Project
from data_connections import DataConnection

from place_file import PlaceFile
from get_file import GetFile
from cloud import CloudManager

from clihandler import CliHandler

from util import version, success, failed, sizestr

logger = logging.getLogger()

class Controller(socketserver.ThreadingMixIn, socketserver.TCPServer):
    # pylint: disable=too-many-public-methods
    # pylint: disable=too-many-instance-attributes

    TIMEOUT_BACKUP = 60 * 60 * 8 #  = 28800 seconds = 8 hours
    CLI_URI = "/cli"
    allow_reuse_address = True

    DATA_DIR = "Data"
    BACKUP_DIR = "tableau-backups"
    LOG_DIR = "tableau-logs"
    WORKBOOKS_DIR = "tableau-workbooks"
    DATASOURCES_DIR = "tableau-datasources"
    WORKBOOKS_REFRESH_DIR = "tableau-workbooks-refresh"
    DATASOURCES_REFRESH_DIR = "tableau-datasources-refresh"
    PALETTE_DIR = "palette-system"

    STAGING_DIR = "staging"

    FILENAME_FMT = "%Y%m%d_%H%M%S"

    # mixin-like functionality
    support_case = support_case

    def backup_cmd(self, agent, userid):
        """Perform a backup - not including any necessary migration."""
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-statements

        # FIXME: ensure that the returned body is a superset of FileEntry.api()

        if userid == None:
            auto = True     # It is an 'automatic/scheduled' backup
        else:
            auto = False    # It was requested by a specific user

        min_disk_needed = 1024 * 1024

        # Disk space check.
        try:
            dcheck = DiskCheck(self, agent, self.BACKUP_DIR,
                               FileManager.FILE_TYPE_BACKUP, min_disk_needed)
        except DiskException, ex:
            return self.error(str(ex))

        if dcheck.target_type == FileManager.STORAGE_TYPE_CLOUD:
            logger.debug("Backup will copy to cloud storage type %s " + \
                         "name '%s' bucket '%s'",
                         dcheck.target_entry.cloud_type,
                         dcheck.target_entry.name,
                         dcheck.target_entry.bucket)
        elif dcheck.target_type == FileManager.STORAGE_TYPE_VOL:
            if dcheck.target_entry.agentid == agent.agentid:
                logger.debug("Backup will stay on the primary.")
            else:
                logger.debug("Backup will copy to target '%s', target_dir '%s'",
                             dcheck.target_agent.displayname, dcheck.target_dir)
        else:
            logger.error("backup_cmd: Invalid target_type: %s",
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
        body = self.cli_cmd(cmd, agent, timeout=self.TIMEOUT_BACKUP)
        backup_elapsed_time = time.time() - backup_start_time

        if body.has_key('error'):
            body['info'] = 'Backup command elapsed time before failure: %s' % \
                            self.seconds_to_str(backup_elapsed_time)
            return body

        backup_size = 0
        try:
            backup_size_body = agent.filemanager.filesize(backup_full_path)
        except IOError as ex:
            logger.error("filemanager.filesize('%s') failed: %s",
                         backup_full_path, str(ex))
        else:
            if not success(backup_size_body):
                logger.error("Failed to get size of backup file '%s': %s",
                             backup_full_path, backup_size_body['error'])
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

        body['fileid'] = place.placed_file_entry.fileid # needed by webapp
        body['info'] += '\n' + stats

        body['size'] = sizestr(backup_size)
        body['destination_type'] = place.placed_file_entry.storage_type
        if place.placed_file_entry.storage_type == \
                                        FileManager.STORAGE_TYPE_CLOUD:
            # cloud type (s3 or gcs, etc.)
            body['destination_name'] = dcheck.target_entry.cloud_type
            # bucket
            body['destination_location'] = '%s - %s' % \
                            (dcheck.target_entry.bucket,
                            os.path.join(dcheck.parent_dir, place.name_only))
        else:
            if not place.copy_failed:
                # displayname
                body['destination_name'] = dcheck.target_agent.displayname
                # volume + pathname
                body['destination_location'] = dcheck.target_dir
            else:
                # Copy failed, so still on the primary
                body['destination_name'] = agent.displayname
                # volume + pathname
                body['destination_location'] = agent.path.dirname(
                                                             place.full_path)
        return body

    def rotate_backups(self):
        """Rotate/delete old auto-generated and then user-generated
           backup files."""
        file_type = FileManager.FILE_TYPE_BACKUP
        find_method = self.files.find_by_auto_envid
        find_name = "scheduled"

        auto_retain = self.system[SystemKeys.BACKUP_AUTO_RETAIN_COUNT]
        info = self.file_rotate(auto_retain, find_method, find_name, file_type)

        find_method = self.files.find_by_non_auto_envid
        find_name = "user generated"

        user_retain = self.system[SystemKeys.BACKUP_USER_RETAIN_COUNT]
        info += self.file_rotate(user_retain, find_method, find_name, file_type)

        return info

    def rotate_ziplogs(self):
        """Rotate/delete old ziplog files."""
        file_type = FileManager.FILE_TYPE_ZIPLOG
        find_method = self.files.find_by_auto_envid
        find_name = "scheduled"

        auto_retain = self.system[SystemKeys.ZIPLOG_AUTO_RETAIN_COUNT]
        info = self.file_rotate(auto_retain, find_method, find_name, file_type)

        find_method = self.files.find_by_non_auto_envid
        find_name = "user generated"

        user_retain = self.system[SystemKeys.ZIPLOG_USER_RETAIN_COUNT]
        info += self.file_rotate(user_retain, find_method, find_name, file_type)

        return info

    def file_rotate(self, retain_count, find_method, find_name, file_type):
        """Delete the old files."""

        rows = find_method(self.environment.envid, file_type)

        if retain_count == -1:
            info = ("\nThere are %d %s %s files.  The configuration is to " + \
                    "retain all %s %s files.") % \
                    (len(rows), find_name, file_type, find_name, file_type)
            logger.debug(info)
            return info

        remove_count = len(rows) - retain_count
        if remove_count <= 0:
            remove_count = 0
            info = ""
        else:
            info = ("\nThere are %d %s %s files.  Retaining %d.  " + \
                   "Will remove %d.") % \
                   (len(rows), find_name, file_type,
                   retain_count, remove_count)

            logger.debug(info)

        for entry in rows[:remove_count]:
            logger.debug("file_rotate: deleting %s file type " +
                         "%s name %s fileid %d", find_name, file_type,
                         entry.name, entry.fileid)
            body = self.files.delfile_by_entry(entry)
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

    def status_cmd(self, agent):
        return self.cli_cmd('tabadmin status -v', agent, timeout=60*5)

    def public_url(self):
        """ Generate a url for Tableau that is reportable to a user."""
        url = self.system[SystemKeys.TABLEAU_SERVER_URL]
        if url:
            return url

        key = 'svcmonitor.notification.smtp.canonical_url'
        url = self.yml.get(key, default=None)
        if url:
            return url

        return None

    def tabcmd(self, args, agent):
        cred = self.cred.get('primary', default=None)
        if cred is None:
            cred = self.cred.get('secondary', default=None)
            if cred is None:
                errmsg = 'No credentials found.'
                logger.error('tabcmd: ' + errmsg)
                return {'error': 'No credentials found.'}
        pw = cred.getpasswd()
        if not cred.user or not pw:
            errmsg = 'Invalid credentials.'
            logger.error('tabcmd: ' + errmsg)
            return {'error': errmsg}
        url = self.system[SystemKeys.TABLEAU_INTERNAL_SERVER_URL]
        if not url:
            url = self.system[SystemKeys.TABLEAU_SERVER_URL]
        if not url:
            errmsg = 'No local URL available.'
            return {'error': errmsg}
        # tabcmd options must come last.
        cmd = ('tabcmd %s -u %s --password %s ' + \
               '--no-cookie --server %s --no-certcheck --timeout %d') %\
              (args, cred.user, pw, url, self.system[SystemKeys.TABCMD_TIMEOUT])
        return self.cli_cmd(cmd, agent,
                                timeout=self.system[SystemKeys.TABCMD_TIMEOUT])

    def kill_cmd(self, xid, agent):
        """Send a "kill" command to an Agent to end a process by XID.
            Returns the body of the reply.
            Called without the connection lock."""

        logger.debug("kill_cmd")
        aconn = agent.connection
        aconn.lock()
        logger.debug("kill_cmd got lock")

        data = {'action': 'kill', 'xid': xid}
        send_body = json.dumps(data)

        headers = {"Content-Type": "application/json"}
        uri = self.CLI_URI

        logger.debug('about to send the kill command, xid %d', xid)
        try:
            aconn.httpconn.request('POST', uri, send_body, headers)
            logger.debug('sent kill command')
            res = aconn.httpconn.getresponse()
            logger.debug('command: kill: ' + \
                               str(res.status) + ' ' + str(res.reason))
            body_json = res.read()
            if res.status != httplib.OK:
                logger.error("kill_cmd: POST failed: %d\n", res.status)
                alert = "Agent command failed with status: " + str(res.status)
                self.remove_agent(agent, alert)
                return self.httperror(res, method="POST",
                                      displayname=agent.displayname,
                                      uri=uri, body=body_json)

            logger.debug("headers: " + str(res.getheaders()))

        except (httplib.HTTPException, EnvironmentError) as ex:
            # bad agent
            msg = "kill_cmd: failed: " + str(ex)
            logger.error(msg)
            self.remove_agent(agent, "Command to agent failed. " \
                                  + "Error: " + str(ex))
            return self.error(msg)
        finally:
            # Must call aconn.unlock() even after self.remove_agent(),
            # since another thread may waiting on the lock.
            aconn.unlock()
            logger.debug("kill_cmd unlocked")

        logger.debug("done reading.")
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
                logger.info("copy_cmd: agent with conn_id %d is now " + \
                            "gone anqd won't be checked.", key)
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
            logger.debug("Enabling firewall port %d on src host '%s'", \
                         src.listen_port, src.displayname)
            fw_body = src.firewall.enable([src.listen_port])
            if fw_body.has_key("error"):
                logger.error("firewall enable port %d on src host %s " + \
                             "failed with: %s", src.listen_port,
                             src.displayname, fw_body['error'])
                data = agent.todict()
                data['error'] = fw_body['error']
                data['info'] = "Port " + str(src.listen_port)
                self.event_control.gen(EventControl.FIREWALL_OPEN_FAILED, data)
                return fw_body

        source_ip = src.ip_address

       # Make sure the target directory on the target agent exists.
        try:
            dst.filemanager.mkdirs(target_dir)
        except (IOError, ValueError) as ex:
            logger.error("copycmd: Could not create directory: '%s': %s",
                         target_dir, ex)
            error = "Could not create '%s' on target agent '%s': %s" % \
                    (target_dir, dst.displayname, ex)
            return self.error(error)

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
            logger.error("Source agent not found!  agentid: %d", src.agentid)
            return self.error("Source agent not found: %d " % src.agentid)

        env = {u'BASIC_USERNAME': entry.username,
               u'BASIC_PASSWORD': entry.password}

        logger.debug("agent username: %s, password: %s",
                     entry.username, entry.password)

        # Send command to target agent
        copy_body = self.cli_cmd(command, dst, env=env)
        if success(copy_body):
            filename = src.path.basename(source_path)
            copy_body['path'] = dst.path.join(target_dir, filename)
        return copy_body

    def restore_local(self, agent, path, userid=None,
                      data_only=False, run_as_password=None):
        """
        Do a restore from a file located on the primary.
          agent: primary agent
          path: path to the tsbak
        NOTE: the caller is responsible for restoring the original state.
        """
        # pylint: disable=too-many-arguments
        data = agent.todict()
        if data_only:
            data['restore_type'] = 'Data only'
        else:
            data['restore_type'] = 'Data and Configuration'

        # The restore file is now on the Primary Agent.
        self.event_control.gen(EventControl.RESTORE_STARTED,
                               data, userid=userid)

        reported_status = self.statusmon.get_tableau_status()

        if reported_status == TableauProcess.STATUS_RUNNING:
            # Restore can run only when tableau is stopped.
            self.state_manager.update(StateManager.STATE_STOPPING_RESTORE)
            logger.debug("----------Stopping Tableau for restore-----------")
            stop_body = self.cli_cmd("tabadmin stop", agent, timeout=60*60)
            if stop_body.has_key('error'):
                logger.info("Restore: tabadmin stop failed")
                return stop_body

            self.event_control.gen(EventControl.STATE_STOPPED, data,
                                   userid=userid)

        # NOTE: no handling of the maint webserver.
        self.state_manager.update(StateManager.STATE_STARTING_RESTORE)

        cmd = 'tabadmin restore \\\"%s\\\"' % path
        if run_as_password:
            cmd += ' --password \\\"%s\\\"' % run_as_password
        if data_only:
            cmd += ' --no-config'

        env = {u'PWD': agent.data_dir}

        try:
            logger.debug("restore sending command: %s", cmd)
            restore_body = self.cli_cmd(cmd, agent, env=env,
                                        timeout=self.TIMEOUT_BACKUP)
        except httplib.HTTPException, ex:
            restore_body = {"error": "HTTP Exception: " + str(ex)}
        return restore_body


    def restore_cmd(self, agent, backup_full_path, orig_state,
                    no_config=False, userid=None, user_password=None):
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

        data = agent.todict()
        if no_config:
            data['restore_type'] = 'Data only'
        else:
            data['restore_type'] = 'Data and Configuration'

        # If the backup file is not on the primary agent (other agent
        # or cloud storage), copy the file from the other agent or
        # cloud storage to the staging area on the primary.
        try:
            got = GetFile(self, agent, backup_full_path)
        except IOError as ex:
            self.state_manager.update(orig_state)
            return self.error("restore_cmd failure: %s" % str(ex))

        # The restore file is now on the Primary Agent.
        restore_body = self.restore_local(agent, got.primary_full_path,
                                          userid=userid, data_only=no_config,
                                          run_as_password=user_password)

        if failed(restore_body):
            self.state_manager.update(orig_state)

        # fixme: Do we need to add restore information to the database?
        # fixme: check status before cleanup? Or cleanup anyway?

        info = ''
        if got.copied:
            # If the file was copied to the Primary, delete
            # the temporary backup file we copied to the Primary.
            delete_body = self.files.delete_vol_file(agent,
                                                 got.primary_full_path)
            if 'error' in delete_body:
                info += '\n' + delete_body['error']

        if info:
            restore_body['info'] = info.strip()

        return restore_body

    def restore_url(self, agent, url, userid=None,
                    data_only=False, run_as_password=None):
        """ Restore from an arbitrary file specified by urlstring.
        The 'agent' parameter is the primary agent for the environment (hack)
        """
        # pylint: disable=too-many-arguments
        envid = self.environment.envid
        cleanup_file = False # should the file on the primary be deleted.

        if isinstance(url, basestring):
            url = urlsplit(url)

        path = urllib.unquote(url.path)
        if url.scheme == 'file':
            if path.startswith('/.') or agent.iswin:
                # '/.' allows files to be specified relative to the data-dir
                # and all windows paths start after the initial '/'
                path = path[1:]

            # an unspecified url.hostname means on the primary
            if url.hostname:
                agentid = Agent.get_agentid_from_host(envid, url.hostname)
                if agent.agentid != agentid:
                    # The PaletteArchiveServer doesn't support generic files
                    # yet so this can't be relied upon.
                    #
                    # body = self.copy_cmd(agentid, path,
                    #                      agent.agentid, agent.data_dir)
                    body = {'status': 'FAILED',
                            'error': 'Cannot yet restore by URL from a worker.'}
                    if failed(body):
                        return body
                    cleanup_file = True
                    path = body['path']
        elif url.scheme in ('s3', 'gcs'):
            body = self.cloud.download(agent, url)
            if failed(body):
                return body
            cleanup_file = True
            path = body['path']

        restore_body = self.restore_local(agent, path, userid=userid,
                                          data_only=data_only,
                                          run_as_password=run_as_password)
        if cleanup_file:
            # best effort here
            agent.filemanager.delete(path)
        return restore_body

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

    def odbc_ok(self):
        """Reports back True if odbc commands can be run now to
           the postgres database.  odbc commands should be not sent
           in these cases:
            * When the tableau is stopped, since the postgres is also
              stopped when tableau is stopped.
            * When in "UPGRADE" mode.
           The primary should be enabled before doing an odbc connection,
           but that should be been handled in the "get_agent" call.
        """
        main_state = self.state_manager.get_state()
        if main_state in (StateManager.STATE_DISCONNECTED,
                          StateManager.STATE_PENDING,
                          StateManager.STATE_STOPPING,
                          StateManager.STATE_STOPPING_RESTORE,
                          StateManager.STATE_STOPPED,
                          StateManager.STATE_STOPPED_UNEXPECTED,
                          StateManager.STATE_STOPPED_RESTORE,
                          StateManager.STATE_STARTING,
                          StateManager.STATE_STARTING_RESTORE,
                          StateManager.STATE_RESTARTING,
                          StateManager.STATE_UPGRADING):
            return False
        else:
            return True

    def active_directory_verify(self, agent, windomain, username, password):
        data = {'domain': windomain, 'username':username, 'password':password}
        body = agent.connection.http_send_json('/ad', data)
        return json.loads(body)

    def get_pinfo(self, agent, update_agent=False):
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
            logger.error("Bad json from pinfo. Error: %s, json: %s", \
                         str(ex), json_str)
            raise IOError("Bad json from pinfo.  Error: %s, json: %s" % \
                          (str(ex), json_str))
        if pinfo is None:
            logger.error("Bad pinfo output: %s", json_str)
            raise IOError("Bad pinfo output: %s" % json_str)

        # When we are called from init_new_agent(), we don't know
        # the agent_type yet and update_agent_pinfo_vols() needs to
        # know the agent type for the volume table values.
        # When we are called by do_info() we will know the agent type.
        if update_agent:
            if agent.agent_type:
                self.agentmanager.update_agent_pinfo_dirs(agent, pinfo)
                self.agentmanager.update_agent_pinfo_vols(agent, pinfo)
                self.agentmanager.update_agent_pinfo_other(agent, pinfo)
            else:
                logger.error("get_pinfo: Could not update agent: unknown " + \
                             "displayname.  uuid: %s", agent.uuid)
                raise IOError("get_pinfo: Could not update agent: unknown " + \
                              "displayname.  uuid: %s" % agent.uuid)
        return pinfo

    def get_info(self, agent, update_agent=False):
        # FIXME: catch errors.
        body = agent.connection.http_send('GET', '/info')

        try:
            info = json.loads(body)
        except ValueError, ex:
            logger.error("Bad json from info. Error: %s, json: %s", \
                         str(ex), body)
            raise IOError("Bad json from pinfo.  Error: %s, json: %s" % \
                          (str(ex), body))
        if info is None:
            logger.error("Bad info output: %s", body)
            raise IOError("Bad info output: %s" % body)

        # When we are called from init_new_agent(), we don't know
        # the agent_type yet and update_agent_pinfo_vols() needs to
        # know the agent type for the volume table values.
        # When we are called by do_info() we will know the agent type.
        if update_agent:
            if agent.agent_type:
                self.agentmanager.update_agent_pinfo_dirs(agent, info)
                self.agentmanager.update_agent_pinfo_vols(agent, info)
                self.agentmanager.update_agent_pinfo_other(agent, info)
            else:
                logger.error("get_info: Could not update agent: unknown " + \
                             "displayname.  uuid: %s", agent.uuid)
                raise IOError("get_pinfo: Could not update agent: unknown " + \
                              "displayname.  uuid: %s" % agent.uuid)

        return info

    def yml_sync(self, agent, set_agent_types=True):
        """Note: Can raise an IOError (if the filemanager.get() fails)."""
        old_gateway_hosts = self.yml.get('gateway.hosts', default=None)
        body = self.yml.sync(agent)
        new_gateway_hosts = self.yml.get('gateway.hosts', default=None)

        if set_agent_types:
            # See if any worker agents need to be reclassified as
            # archive agents or vice versa.
            self.agentmanager.set_all_agent_types()

        if not old_gateway_hosts is None:
            if old_gateway_hosts != new_gateway_hosts:
                # Stop the maintenance web server, to get out of the way
                # of Tableau if the yml has changed from last check.
                self.maint("stop")

        return body

    def sync_cmd(self, agent, check_odbc_state=True):
        """sync/copy tables from tableau to here."""
        # pylint: disable=too-many-branches

        if check_odbc_state and not self.odbc_ok():
            main_state = self.state_manager.get_state()
            logger.info("Failed.  Current state: %s", main_state)
            msg = "Cannot run command while in state: " + str(main_state)
            raise exc.InvalidStateError(msg)

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

        if not 'status' in sync_dict:
            if 'error' in sync_dict:
                sync_dict['status'] = 'FAILED'
            else:
                sync_dict['status'] = 'OK'

        return sync_dict

    def maint(self, action, agent=None, send_alert=True):
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        """If agent is not specified, action is done for all gateway agents."""
        if action not in ("start", "stop"):
            logger.error("Invalid maint action: %s", action)
            return self.error("Bad maint action: %s" % action)

        envid = self.environment.envid

        manager = self.agentmanager
        try:
            gateway_hosts = manager.get_yml_list('gateway.hosts')
        except ValueError:
            logger.error("maint: %s: No yml entry for 'gateway.hosts' yet.",
                         action)
            return self.error("maint %s: No yml entry for 'gateway.hosts'." % \
                              action)

        # We're going to combine stdout/stderr/error for all gateway hosts.
        body_combined = {'stdout': "",
                         'stderr': "",
                         'error': ""}

        maint_success = True
        send_maint_body = self.set_maint_body(action)

        # We were called with a specific agent so do the maint action only
        # there.
        if agent:
            body = self.send_maint(action, agent, send_maint_body)
            self.update_maint_status(action, body)

            if send_alert:
                self.send_maint_event(action, agent, body)
            return body

        agent_connected = None
        for host in gateway_hosts:
            # This means the primary is the gateway host
            if host == 'localhost' or host == '127.0.0.1':
                agent = manager.agent_by_type(AgentManager.AGENT_TYPE_PRIMARY)
                if not agent:
                    logger.debug("maint: %s: primary is not [yet] " + \
                                 "fully connected.  Skipping.", action)
                    continue

            else:
                agentid = Agent.get_agentid_from_host(envid, host)
                if not agentid:
                    logger.info("maint: %s: No such agent found " + \
                                "for host '%s' from gateway.hosts list: %s",
                                action, host, str(gateway_hosts))
                    continue

                agent = manager.agent_by_id(agentid)
                if not agent:
                    logger.debug("maint: %s: Agent host '%s' with " + \
                                 "agentid %d not connected. " + \
                                 "gateway.hosts list: %s",
                                 action, host, agentid, str(gateway_hosts))
                    continue

            # We have a gateway agent.  Do the maint action if possible.
            if not agent.connection:
                logger.debug("maint: gateway agent not connected: %s. " + \
                             "Skipping '%s'.", host, action)
                continue

            if not agent_connected:
                # The agent to use for the event
                agent_connected = agent

            body = self.send_maint(action, agent, send_maint_body)

            if 'stdout' in body:
                text = '%s: %s\n' % (agent.displayname, body['stdout'])
                body_combined['stdout'] += text
            if 'stderr' in body:
                text = '%s: %s\n' % (agent.displayname, body['stderr'])
                body_combined['stderr'] += text
            if 'error' in body:
                text = '%s: %s\n' % (agent.displayname, body['error'])
                body_combined['error'] += text
                maint_success = False

        if not agent_connected:
            logger.debug("maint: No agents are connected.  Did nothing.")
            body_combined['error'] = "No agents are connected."
            return body_combined    # Empty as we did nothing

        if maint_success:
            # The existence of 'error' signifies failure but all succeeded.
            del body_combined['error']

        self.update_maint_status(action, body_combined)

        if send_alert:
            self.send_maint_event(action, agent_connected, body_combined)

        return body_combined

    def update_maint_status(self, action, body):
        if action == 'start':
            if failed(body):
                self.maint_started = False
            else:
                self.maint_started = True

        elif action == 'stop':
            if failed(body):
                self.maint_started = True
            else:
                self.maint_started = False

    def send_maint(self, action, agent, send_maint_body):
        """Does the actual sending of the maint command to the agent,
           returns the body/result.
        """

        logger.debug("maint: %s for '%s'", action, agent.displayname)
        body = self.send_immediate(agent, "POST", "/maint", send_maint_body)

        return body

    def send_maint_event(self, action, agent, body):
        """Generates the appropriate maint event (start failed, stop
           failed, maint online, maint offline).
        """
        if 'error' in body:
            data = agent.todict()
            if action == "start":
                self.event_control.gen(EventControl.MAINT_START_FAILED,
                                       dict(body.items() + data.items()))
                return
            else:
                self.event_control.gen(EventControl.MAINT_STOP_FAILED,
                                       dict(body.items() + data.items()))
                return

        if action == 'start':
            self.event_control.gen(EventControl.MAINT_ONLINE,
                                   agent.todict())
        else:
            self.event_control.gen(EventControl.MAINT_OFFLINE,
                                   agent.todict())

    def set_maint_body(self, action):
        send_body = {"action": action}

        gateway_ports = self.yml.get('gateway.ports', default=None)
        if gateway_ports:
            ports = gateway_ports.split(';')
            try:
                listen_port = int(ports[0])
                send_body["listen-port"] = listen_port
            except StandardError:
                logger.error("Invalid yml entry for 'gatway.ports': %s",
                             gateway_ports)

        ssl_enabled = self.yml.get('ssl.enabled', default=None)
        if ssl_enabled != 'true':
            return send_body

        ssl_port = self.yml.get('ssl.port', default=None)
        if ssl_port:
            try:
                ssl_port = int(ssl_port)
                send_body['ssl-listen-port'] = ssl_port
            except StandardError:
                logger.error("Invalid yml entry for 'ssl.listen.port': %s",
                             ssl_port)

        # Mapping from the yml file to the json to send.
        file_map = {'ssl.cert.file': 'ssl-cert-file',
                    'ssl.key.file': 'ssl-cert-key-file',
                    'ssl.chain.file': 'ssl-cert-chain-file'}

        for key in file_map.keys():
            value = self.yml.get(key, default=None)
            if not value:
                continue

            send_body[file_map[key]] = value

        return send_body

    def archive(self, action, agent=None, port=-1):
        """'start' or 'stop' one or all archive servers."""
        send_body = {"action": action}
        if port > 0:
            send_body["port"] = port

        if agent:
            # Send archive command to just one agent
            return self.send_immediate(agent, "POST", "/archive", send_body)

        # Send archive command to all connected agents
        body_combined = {'stdout': "",
                         'stderr': "",
                         'error': ""}

        archive_success = True
        agents = self.agentmanager.all_agents()
        for key in agents.keys():
            self.agentmanager.lock()
            if not agents.has_key(key):
                logger.info("archive: agent with conn_id %d is now " + \
                            "gone and won't be checked.", key)
                self.agentmanager.unlock()
                continue
            agent = agents[key]
            self.agentmanager.unlock()
            body = self.send_immediate(agent, "POST", "/archive", send_body)
            if 'stdout' in body:
                stdout = '%s: %s\n' % (agent.displayname, body['stdout'])
                body_combined['stdout'] += stdout
                stderr = '%s: %s\n' % (agent.displayname, body['stderr'])
                body_combined['stderr'] += stderr
                error = '%s: %s\n' % (agent.displayname, body['error'])
                body_combined['error'] += error
                archive_success = False

        if archive_success:
            # The existence of 'error' signifies failure but all succeeded.
            del body_combined['error']
        return body_combined

    def ping(self, agent):
        return self.send_immediate(agent, "POST", "/ping",
                                   {'cpu-monitored-processes': AlertSetting.get_monitored(AlertSetting.CPU),
                            'memory-monitored-processes': AlertSetting.get_monitored(AlertSetting.MEMORY)})

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

        logger.debug("sending an immediate command to '%s', conn_id %d, " + \
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
                logger.error("immediate command to %s failed "
                             "with status %d: %s %s, body: %s:",
                             agent.displayname, res.status,
                             method, uri, rawbody)
                self.remove_agent(agent,\
                                  ("Communication failure with agent. " +\
                                   "Immediate command to %s, status: " +\
                                   "%d: %s %s, body: %s") % \
                                  (agent.displayname, res.status,
                                   method, uri, rawbody))
                return self.httperror(res, method=method,
                                      displayname=agent.displayname,
                                      uri=uri, body=rawbody)
            elif rawbody:
                body = json.loads(rawbody)
            else:
                body = {}
        except (httplib.HTTPException, EnvironmentError) as ex:
            logger.error("Agent send_immediate command %s %s failed: %s",
                         method, uri, str(ex))
            self.remove_agent(agent, \
                            "Agent send_immediate command %s %s failed: %s" % \
                            (method, uri, str(ex)))
            return self.error("send_immediate method %s, uri %s failed: %s" % \
                              (method, uri, str(ex)))
        finally:
            aconn.unlock()

        logger.debug("send immediate %s %s success, conn_id %d, response: %s",
                     method, uri, aconn.conn_id, str(body))
        return body

    def displayname_cmd(self, aconn, uuid, displayname):
        """Sets displayname for the agent with the given hostname. At
           this point assumes uuid is unique in the database."""

        self.agentmanager.set_displayname(aconn, uuid, displayname)

    def ziplogs_cmd(self, agent, userid=None):
        """Run tabadmin ziplogs."""
        # pylint: disable=too-many-locals

        data = agent.todict()

        if userid == None:
            auto = True     # It is an 'automatic/scheduled' ziplogs
        else:
            auto = False    # It was requested by a specific user

        # fixme: get more accurate estimate of ziplog size
        min_disk_needed = 1024 * 1024
        # Disk space check.
        try:
            dcheck = DiskCheck(self, agent, self.LOG_DIR,
                               FileManager.FILE_TYPE_ZIPLOG, min_disk_needed)
        except DiskException, ex:
            data['error'] = str(ex)
            self.event_control.gen(EventControl.ZIPLOGS_FAILED,
                                   data, userid=userid)
            logger.error("ziplogs_cmd: %s", str(ex))
            return self.error("ziplogs_cmd: %s" % str(ex))

        self.event_control.gen(EventControl.ZIPLOGS_STARTED,
                               data, userid=userid)

        ziplogs_name = time.strftime(self.FILENAME_FMT) + ".logs.zip"
        ziplogs_full_path = agent.path.join(dcheck.primary_dir, ziplogs_name)
        cmd = 'tabadmin ziplogs -f -l -n -a \\\"%s\\\"' % ziplogs_full_path
        body = self.cli_cmd(cmd, agent, timeout=60*60*3)    # 3 hours max
        body[u'info'] = unicode(cmd)

        if success(body):
            ziplog_size = 0
            try:
                ziplog_size_body = agent.filemanager.filesize(ziplogs_full_path)
            except IOError as ex:
                logger.error("filemanager.filesize('%s') failed: %s",
                             ziplogs_full_path, str(ex))
            else:
                if not success(ziplog_size_body):
                    logger.error("Failed to get size of ziplogs file %s: %s",
                                 ziplogs_full_path, ziplog_size_body['error'])
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
                                   dict(body.items() + data.items()),
                                   userid=userid)
        else:
            self.event_control.gen(EventControl.ZIPLOGS_FINISHED,
                                   dict(body.items() + data.items()),
                                   userid=userid)
        return body

    def cleanup_cmd(self, agent, userid=None):
        """Run tabadmin cleanup'."""

        data = agent.todict()
        self.event_control.gen(EventControl.CLEANUP_STARTED, data,
                               userid=userid)
        body = self.cli_cmd('tabadmin cleanup', agent, timeout=60*60)
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

        body = {'version_previous': self.previous_version,
                'version_current': self.version}

        system_key = SystemKeys.CONTROLLER_INITIAL_START
        controller_initial_start = self.system[system_key]

        if not controller_initial_start:
            self.system.save(SystemKeys.CONTROLLER_INITIAL_START, True)
            self.event_control.gen(EventControl.CONTROLLER_STARTED, body)
        else:
            self.event_control.gen(EventControl.CONTROLLER_RESTARTED, body)

        if self.version != self.previous_version:
            self.event_control.gen(EventControl.PALETTE_UPDATED, body)

        return

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

        logger.debug("info returned from %s: %s",
                     aconn.displayname, str(pinfo))
        # Set the type of THIS agent.
        if tableau_install_dir in pinfo:
            # FIXME: don't duplicate the data
            agent.agent_type = AgentManager.AGENT_TYPE_PRIMARY
            aconn.agent_type = AgentManager.AGENT_TYPE_PRIMARY

            if pinfo[tableau_install_dir].find(':') == -1:
                logger.error("agent %s is missing ':': %s for %s",
                             aconn.displayname, tableau_install_dir,
                             agent.tableau_install_dir)
                return False
        else:
            if self.agentmanager.is_tableau_worker(agent):
                agent.agent_type = AgentManager.AGENT_TYPE_WORKER
                aconn.agent_type = AgentManager.AGENT_TYPE_WORKER
            else:
                agent.agent_type = AgentManager.AGENT_TYPE_ARCHIVE
                aconn.agent_type = AgentManager.AGENT_TYPE_ARCHIVE

        if agent.iswin:
            self.firewall_manager.do_firewall_ports(agent)

        self.clean_xid_dirs(agent)

        # This saves directory-related info from pinfo: it
        # does not save the volume info since we may not
        # know the displayname yet and the displayname is
        # needed for a disk-usage event report.
        self.agentmanager.update_agent_pinfo_dirs(agent, pinfo)

        # Note: Don't call this before update_agent_pinfo_dirs()
        # (needed for agent.tableau_data_dir).
        if agent.agent_type == AgentManager.AGENT_TYPE_PRIMARY:
            # raises an exception on fail
            self.yml_sync(agent, set_agent_types=False)
            # These can all fail as long as they don't get an IOError.
            # For example, if tableau is stopped, these will fail,
            # but we don't know tableau's status yet and it's
            # worth trying, especially to import the users.
            if success(self.auth.load(agent, check_odbc_state=False)):
                self.sync_cmd(agent, check_odbc_state=False)
                self.extract.load(agent, check_odbc_state=False)
            else:
                logger.debug("init_new_agent: Couldn't do import of " + \
                             "auth, etc. probably due to tableau stopped.")

        # Configuring the 'maint' web server requires the yml file,
        # so this must be done after the "yml_sync()" above.
        self.config_servers(agent)

        return pinfo

    def clean_xid_dirs(self, agent):
        """Remove old XID directories."""
        xid_dir = agent.path.join(agent.data_dir, "XID")
        try:
            body = agent.filemanager.listdir(xid_dir)
        except IOError as ex:
            logger.error("filemanager.listdir('%s') for the XID " + \
                         "directory failed: %s", xid_dir, str(ex))
            return

        if not success(body):
            logger.error("Could not list the XID directory '%s': %s",
                         xid_dir, body['error'])
            return

        if not 'directories' in body:
            logger.error("clean_xid_dirs: Filemanager response missing " + \
                         "directories.  Response: %s", str(body))
            return

        for rem_dir in body['directories']:
            full_path = agent.path.join(xid_dir, rem_dir)
            logger.debug("Removing %s", full_path)
            try:
                agent.filemanager.delete(full_path)
            except IOError as ex:
                logger.error("filemanager.delete('%s') failed: %s",
                             full_path, str(ex))

    def config_servers(self, agent):
        """Configure the maintenance and archive servers."""
        if agent.agent_type in (AgentManager.AGENT_TYPE_PRIMARY,
                                AgentManager.AGENT_TYPE_WORKER):
            # Put into a known state if it could possibly be a
            # gateway server.
            body = self.maint("stop", agent=agent, send_alert=False)
            if body.has_key("error"):
                data = agent.todict()
                self.event_control.gen(EventControl.MAINT_STOP_FAILED,
                                       dict(body.items() + data.items()))

        body = self.archive("stop", agent)
        if body.has_key("error"):
            self.event_control.gen(EventControl.ARCHIVE_STOP_FAILED,
                                   dict(body.items() + agent.todict().items()))
        # Get ready.
        body = self.archive("start", agent)
        if body.has_key("error"):
            self.event_control.gen(EventControl.ARCHIVE_START_FAILED,
                                   dict(body.items() + agent.todict().items()))

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

    def upgrade_version(self):
        """Make changes to the database, etc. as required for upgrading
           from last_version to new_version."""

        logger.debug("Upgrade from %s to %s",
                     self.previous_version, self.version)

        if self.previous_version == self.version or not self.previous_version:
            return

        if self.previous_version[:4] == '1.5.':
            # Upgrade from 1.5 to 1.6
            self.workbooks.move_twb_to_db()

        if self.previous_version[:2] == '2.':
            return

        # Upgrade to 2.0
        if self.system[SystemKeys.WORKBOOK_ARCHIVE_ENABLED]:
            # Retain count of 0 used to be unlimited but now -1 is
            # unlimited and 0 is disabled.
            if self.system[SystemKeys.WORKBOOK_RETAIN_COUNT] == 0:
                self.system.save(SystemKeys.WORKBOOK_RETAIN_COUNT, -1)
        else:
            self.system.save(SystemKeys.WORKBOOK_RETAIN_COUNT, 0)

        if self.system[SystemKeys.DATASOURCE_ARCHIVE_ENABLED]:
            if self.system[SystemKeys.DATASOURCE_RETAIN_COUNT] == 0:
                self.system.save(SystemKeys.DATASOURCE_RETAIN_COUNT, -1)
        else:
            self.system.save(SystemKeys.DATASOURCE_RETAIN_COUNT, 0)

class StreamLogger(object):
    """
    File-like stream class that writes to a logger.
    Used for redirecting stdout & stderr to the log file.
    """

    def __init__(self, tag=None):
        self.tag = tag
        # writes are buffered to ensure full lines are printed together.
        self.buf = ''

    def writeln(self, line):
        line = line.rstrip()
        if not line:
            return
        if self.tag:
            line = '[' + self.tag + '] ' + line
        logger.error(line)

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
    """ server main() """
    # pylint: disable=attribute-defined-outside-init
    # pylint: disable=too-many-statements
    # FIXME: 83/50!

    import argparse
    from .logger import make_loggers

    parser = argparse.ArgumentParser(description='Palette Controller')
    parser.add_argument('config', nargs='?', default=None)
    parser.add_argument('--nostatus', action='store_true', default=False)
    parser.add_argument('--noping', action='store_true', default=False)
    parser.add_argument('--nosched', action='store_true', default=False)
    args = parser.parse_args()

    config = Config(args.config)
    host = config.get('controller', 'host', default='localhost')
    port = config.getint('controller', 'port', default=9000)

    # loglevel at the start, here, is controlled by the INI file,
    # though uses a default.  After the database is available,
    # we reset the log-level, depending on the 'debug-level' value in the
    # system table.
    make_loggers(config)
    logger.info("Controller version: %s", version())

    # Log stderr to the log file too.
    # NOTE: stdout is not logged so that PDB will work.
    sys.stderr = StreamLogger(tag='STD')

    # database configuration
    url = config.get("database", "url")
    echo = config.getboolean("database", "echo", default=False)
    max_overflow = config.getint("database", "max_overflow", default=10)

    # engine is once per single application process.
    # see http://docs.sqlalchemy.org/en/rel_0_9/core/connections.html
    meta.create_engine(url, echo=echo, max_overflow=max_overflow)
    meta.Session.autoflush = False
    meta.Session.expire_on_commit = False

    server = Controller((host, port), CliHandler)
    server.config = config

    server.cli_get_status_interval = \
      config.getint('controller', 'cli_get_status_interval', default=10)
    server.noping = args.noping
    server.event_debug = config.getboolean('default',
                                           'event_debug',
                                           default=False)
    Domain.populate()
    server.domainname = config.get('palette', 'domainname')
    server.domain = Domain.get_by_name(server.domainname)
    Environment.populate()
    server.environment = Environment.get()

    AlertSetting.prepare()
    AlertSetting.populate()

    # Must be the first 'manager'
    server.system = SystemManager(server)
    SystemManager.populate()

    # Set version info
    server.previous_version = server.system[SystemKeys.PALETTE_VERSION]
    server.version = version()
    server.system.save(SystemKeys.PALETTE_VERSION, server.version)

    # Set the log level from the system table
    logger.setLevel(server.system[SystemKeys.DEBUG_LEVEL])

    HttpControl.populate()
    StateControl.populate()
    DataSourceTypes.populate()

    server.auth = AuthManager(server)
    server.cred = CredentialManager(server)
    server.extract = ExtractManager(server)
    server.extract_archive = ExtractRefreshManager(server)
    server.hrman = HttpRequestManager(server)

    # Status of the maintenance web server(s)
    server.maint_started = False

    Role.populate()
    UserProfile.populate()

    # Must be done after auth, since it uses the users table.
    server.alert_email = AlertEmail(server)

    # Must be set before EventControlManager
    server.yml = YmlManager(server)

    EventControl.populate_upgrade(server.previous_version, server.version)
    server.event_control = EventControlManager(server)

    # Send controller started/restarted and potentially "new version" events.
    server.controller_init_events()

    server.upgrade_rwlock = RWLock()

    server.workbooks = WorkbookManager(server)
    server.datasources = DataSourceManager(server)
    server.files = FileManager(server)
    server.cloud = CloudManager(server)
    server.firewall_manager = FirewallManager(server)
    server.license_manager = LicenseManager(server)
    server.state_manager = StateManager(server)
#    server.package = Package()
    server.notifications = NotificationManager(server)
    server.metrics = MetricManager(server)

    server.ports = PortManager(server)
    server.ports.populate()

    server.upgrade_version()

    clicmdclass = CliCmd(server)
    server.cli_cmd = clicmdclass.cli_cmd

    manager = AgentManager(server)
    server.agentmanager = manager

    manager.update_last_disconnect_time()

    logger.debug("Starting agent listener.")
    manager.start()

    # Need to instantiate to initialize state and status tables,
    # even if we don't run the status thread.
    statusmon = TableauStatusMonitor(server, manager)
    server.statusmon = statusmon

    if not args.nosched:
        server.sched = Sched(server)
        server.sched.populate()
        # Make sure the populate finishes before the sched thread starts
        server.sched.start()

    if not args.nostatus:
        logger.debug("Starting status monitor.")
        statusmon.start()

    server.serve_forever()
