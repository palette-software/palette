#!/usr/bin/env python

import sys
import os
import SocketServer as socketserver
import socket

import json
import time
import datetime

import exc
from request import *

import httplib
import ntpath

import boto
from boto.exception import AWSConnectionError, BotoClientError, BotoServerError

import sqlalchemy
from sqlalchemy.orm import sessionmaker, scoped_session
from akiri.framework.ext.sqlalchemy import meta

from agentmanager import AgentManager
from agent import Agent
from agentinfo import AgentVolumesEntry
from auth import AuthManager
from backup import BackupManager
from diskcheck import DiskCheck, DiskException
from firewall_manager import FirewallManager
from state import StateManager
from system import SystemManager, LicenseEntry
from tableau import TableauStatusMonitor, TableauProcess
from config import Config
from domain import Domain
from environment import Environment
from profile import UserProfile, Role
from state_control import StateControl
from alert_email import AlertEmail
from event import EventManager
from event_control import EventControl, EventControlManager
from extracts import ExtractManager
from storage import StorageConfig
from workbooks import WorkbookEntry, WorkbookManager

from sites import Site
from projects import Project
from data_connections import DataConnection
from http_requests import HTTPRequestEntry # needed for create_all()

from gcs import GCS
from s3 import S3

from sched import Sched, Crontab # needed for create_all()
from clihandler import CliHandler
from util import version, success, failed, sizestr

class Controller(socketserver.ThreadingMixIn, socketserver.TCPServer):

    CLI_URI = "/cli"
    LOGGER_NAME = "main"
    allow_reuse_address = True

    DATA_DIR = "Data"
    BACKUP_DIR = "tableau-backups"
    LOG_DIR = "tableau-logs"
    WORKBOOKS_DIR = "tableau-workbooks"
    PALETTE_DIR = "palette-system"

    def backup_cmd(self, agent):
        """Perform a backup - not including any necessary migration."""

        # Disk space check.
        try:
            dcheck = DiskCheck(self, agent)
        except DiskException, e:
            return self.error(str(e))

        gcsid = None
        s3id = None

        if dcheck.target_type == StorageConfig.GCS:
            self.log.debug("Backup will copy to gcs named '%s'",
                                                dcheck.target_entry.name)
            cloud_cmd = self.gcs_cmd
            gcsid = dcheck.target_entry.gcsid
        elif dcheck.target_type == StorageConfig.S3:
            self.log.debug("Backup will copy to s3 named '%s'",
                                                dcheck.target_entry.name)
            cloud_cmd = self.s3_cmd
            s3id = dcheck.target_entry.s3id
        elif dcheck.target_type == StorageConfig.VOL:
            if dcheck.target_entry.agentid == agent.agentid:
                self.log.debug("Backup will stay on the primary.")
            else:
                self.log.debug(\
                    "Backup will copy to target '%s', target_dir '%s'",
                        dcheck.target_agent.displayname, dcheck.target_dir)
        else:
            self.log.error("backup_cmd: Invalid target_type: %s" % \
                           dcheck.target_type)
            return self.error("backup_cmd: Invalid target_type: %s" % \
                              dcheck.target_type)
        # Example name: 20140127_162225.tsbak
        backup_name = time.strftime("%Y%m%d_%H%M%S") + ".tsbak"


        # Example: "c:/ProgramData/Palette/Data/tableau-backups/20140127_162225.tsbak"

        if dcheck.target_type == StorageConfig.VOL and \
           dcheck.target_agent.agent_type == \
                   AgentManager.AGENT_TYPE_PRIMARY and \
                           not dcheck.target_is_palette_primary_data_volume:
           # The backup target is on the primary server but not on the
           # the palette primary *directory*. Do the backup directly to the
           # target directory rather than copying it there after the backup.

           # First make sure the target directory on the primary exists.
            try:
                agent.filemanager.mkdirs(dcheck.target_dir)
            except (IOError, ValueError) as e:
                self.log.error(\
                    "backup_cmd: Could not create directory: '%s'" % \
                    dcheck.target_dir)
                body = {'error': str(e),
                        'info': "Could not create backup directory '%s'" % \
                               dcheck.target_dir}
                return body

            # e.g. E:\\ProgramData\Palette\Data\tableau-backups\2014Jan27_162225.tsbak
            backup_full_path = agent.path.join(dcheck.target_dir, backup_name)
        else:
            # The backup will be done to the palette primary data location
            # and then one of, depending on the user configuration:
            # 1) copied to another agent
            # 2) copied to cloud storage,
            # 3) remain right there.
            #
            # Get the vol + dir to use for the backup command to tabadmin.
            palette_data_path = self.backup.palette_primary_data_loc_path(agent)
            # e.g. C:\\ProgramData\Palette\Data\tableau-backups\2014Jan27_162225.tsbak
            backup_full_path = agent.path.join(self.primary_backup_dir(agent),
                                          backup_name)

        cmd = 'tabadmin backup \\\"%s\\\"' % backup_full_path

        backup_start_time = time.time()
        body = self.cli_cmd(cmd, agent)
        backup_elapsed_time = time.time() - backup_start_time

        if body.has_key('error'):
            body['info'] = 'Backup command elapsed time: %s' % \
                            self.seconds_to_str(backup_end_time - start_time)
            return body

        BACKUP_UNKNOWN = -1

        backup_size = BACKUP_UNKNOWN
        backup_size_body = agent.filemanager.filesize(backup_full_path)
        if not success(backup_size_body):
            self.log.error("Failed to get size of backup file %s: %s" %\
                            backup_full_path, backup_size_body['error'])

        backup_size = backup_size_body['size']

        body['info'] = ""
        delete_local_backup = True

        palette_primary_data_dir_vol_entry = \
            self.backup.get_palette_primary_data_loc_vol_entry(agent)

        if not palette_primary_data_dir_vol_entry:
            self.log.error(\
                "Could not retrieve get_palette_primary_data_loc_vol_entry")
            return self.error(
                "Could not retrieve get_palette_primary_data_loc_vol_entry")

        copy_elapsed_time = 0

        if dcheck.target_type in (StorageConfig.GCS, StorageConfig.S3):
            copy_start_time = time.time()
            storage_body = cloud_cmd(agent, "PUT",
                            dcheck.target_entry, backup_full_path)
            copy_end_time = time.time()
            if 'error' in storage_body:
                body['info'] = "Copy to %s '%s' failed: %s" % \
                    (dcheck.target_type, dcheck.target_entry.name,
                                                        storage_body['error'])
                delete_local_backup = False
                self.backup.add(backup_full_path,
                            agentid=palette_primary_data_dir_vol_entry.agentid)
            else:
                copy_elapsed_time = time.time() - copy_start-time
                body['info'] = \
                    ("Backup file was copied to %s bucket '%s' " + \
                     "filename '%s'.") % \
                    (dcheck.target_type, dcheck.target_entry.bucket,
                     backup_name)
                # Backup was copied to gcs or s3
                self.backup.add(backup_name, gcsid=gcsid, s3id=s3id)
                delete_local_backup = True

        elif dcheck.target_agent.agent_type != AgentManager.AGENT_TYPE_PRIMARY:
            # Copy the backup to a non-primary agent
            # Example: "Tableau Archive #202:D/palette-backups/20140127_162225.tsbak"

            (backup_vol, backup_path) = backup_full_path.split(':', 1)

            # Get the path used by routes.txt to find the common prefix
            source_agent_vol_entry = \
                AgentVolumesEntry.get_vol_entry_by_agentid_vol_name(
                                                    agent.agentid, backup_vol)
            if not source_agent_vol_entry:
                return self.error(
                    (u"Could not find backup volume '%s' for agentid %d. " + \
                    "Backup will remain on the primary agent.") % \
                    (backup_vol, agent.agentid))

            common = os.path.commonprefix([backup_path,
                                          source_agent_vol_entry.path])

            if common:
                # Chop off the common part
                backup_path = backup_path[len(common):]

            source_path = "%s:%s%s" % (agent.displayname, backup_vol,
                                        backup_path)
            copy_start_time = time.time()
            copy_body = self.copy_cmd(source_path,
                        dcheck.target_agent.displayname, dcheck.target_dir)

            if copy_body.has_key('error'):
                msg = (u"Copy of backup file '%s' to agent '%s:%s' failed. "+\
                    "Will leave the backup file on the primary agent. " + \
                    "Error was: %s") \
                    % (backup_full_path, dcheck.target_agent.displayname, 
                                    dcheck.target_dir, copy_body['error'])
                self.log.info(msg)
                body['info'] += msg
                # Something was wrong with the copy to the non-primary agent.
                # Leave the backup on the primary after all.
                self.backup.add(backup_full_path,
                            agentid=palette_primary_data_dir_vol_entry.agentid)
                delete_local_backup = False
            else:
                # The copy succeeded.
                copy_elapsed_time = time.time() - copy_start_time()
                body['info'] += \
                    "Backup file copied to agent '%s', directory: %s." % \
                        (dcheck.target_agent.displayname, dcheck.target_dir)

                target_full_path = dcheck.target_agent.path.join(
                                            dcheck.target_dir, backup_name)

                self.backup.add(target_full_path,
                                agentid=dcheck.target_agent.agentid)
                # Remember to remove the backup file from the primary
                delete_local_backup = True
        elif dcheck.target_agent.agent_type == AgentManager.AGENT_TYPE_PRIMARY:
            if dcheck.target_is_palette_primary_data_volume:
                body['info'] += \
                    ('Backup file is configured to stay on ' + \
                    'the Tableau primary agent, ' + \
                    'palette primary data directory: %s') % dcheck.target_dir

                delete_local_backup = False
            else:
                # The tabadmin backup was done directly to the
                # alternate volume on the primary agent.
                body['info'] = ("Backup file is configured to stay on " + \
                    'the Tableau primary agent, non-primary palette ' + \
                    'data directory: %s') % dcheck.target_dir

                delete_local_backup = False
            self.backup.add(backup_full_path,
                            agentid=dcheck.target_agent.agentid)

        if delete_local_backup:
            remove_body = self.delete_file(agent, backup_full_path)
            # Check if the DEL worked.
            if remove_body.has_key('error'):
                body['info'] += \
                    ("\nDeletion of backup file failed after copy. "+\
                        "File: '%s'. Error was: %s") \
                        % (backup_full_path, remove_body['error'])


        # Report backup stats
        total_time = backup_elapsed_time + copy_elapsed_time

        stats = 'Backup size: %s\n' % sizestr(backup_size)
        stats += 'Backup elapsed time: %s (%.1f%%)\n' % \
                  (self.seconds_to_str(backup_elapsed_time),
                   (backup_elapsed_time / total_time) * 100)

        if copy_elapsed_time:
            stats += 'Backup copy elapsed time: %s (%.1f%%)' % \
                     (self.seconds_to_str(copy_elapsed_time),
                     (copy_elapsed_time / total_time) * 100)

            stats += 'Total time: %s' % self.seconds_to_str(total_time)

        body['info'] += stats
        return body


    def seconds_to_str(self, seconds):
            return str(datetime.timedelta(seconds=seconds))

    def primary_backup_dir(self, agent):
        """return the palette primary backup directory."""

        palette_data_path = self.backup.palette_primary_data_loc_path(agent)
        return agent.path.join(palette_data_path,
                               self.DATA_DIR,
                               self.BACKUP_DIR)

    def gcs_cmd(self, agent, action, gcs_entry, full_path):

        land_dir = agent.path.dirname(full_path)

        filename = agent.path.basename(full_path)

        env = {u'ACCESS_KEY': gcs_entry.access_key,
               u'SECRET_KEY': gcs_entry.secret,
               u'PWD': land_dir}

        gcs_command = 'pgcs %s %s "%s"' % (action, gcs_entry.bucket, filename)

        # Send the gcs command to the agent
        return self.cli_cmd(gcs_command, agent, env=env)

    def s3_cmd(self, agent, action, s3_entry, full_path):

        land_dir = agent.path.dirname(full_path)
        #fixme: create the path first

        filename = agent.path.basename(full_path)

        resource = os.path.basename(filename)
        try:
            token = s3_entry.get_token(resource)
        except (AWSConnectionError, BotoClientError, BotoServerError) as e:
            return self.error("s3: %s" % str(e))

        # fixme: this method doesn't work
        env = {u'ACCESS_KEY': token.credentials.access_key,
               u'SECRET_KEY': token.credentials.secret_key,
               u'SESSION': token.credentials.session_token,
               u'REGION_ENDPOINT': s3_entry.region,
               u'PWD': land_dir}

        env = {u'ACCESS_KEY': s3_entry.access_key,
               u'SECRET_KEY': s3_entry.secret,
               u'PWD': land_dir}

        s3_command = 'ps3 %s %s "%s"' % (action, s3_entry.bucket, filename)

        # Send the s3 command to the agent
        return self.cli_cmd(s3_command, agent, env=env)

    def backupdel_cmd(self, backup):
        """Delete a Tableau backup."""

        # FIXME: tie backup to domain

        entry = self.backup.find_by_name(backup)
        if not entry:
            return self.error("no backup found with name: %s" % (backup))

        if not entry.volid:
            return self.error("Can delete only backups on primary and agents.")

        agent_db = Agent.get_agentstatusentry_by_volid(entry.volid)

        agent = self.agentmanager.agent_by_uuid(agent_db.uuid)
        if not agent:
            return self.error("agent not connected: displayname=%s uuid=%s" % \
              (agent_db.displayname, agent_db.uuid))

        vol_entry = AgentVolumesEntry.get_vol_entry_by_volid(entry.volid)
        if not vol_entry:
            return self.error("Missing volume id: %d!" % entry.volid)

        # FIXME: use agent.path
        backup_path = ntpath.join(vol_entry.name + ":", vol_entry.path, backup)
        self.log.debug("backupdel_cmd: Deleting path '%s' on agent '%s'",
                       backup_path, agent.displayname)

        body = self.delete_file(agent, backup_path)
        if not body.has_key('error'):
            try:
                self.backup.remove(entry.backupid)
            except sqlalchemy.orm.exc.NoResultFound:
                return self.error("backup not found name=%s agent=%s" % \
              (backup, agent.displayname))

        return body

    def status_cmd(self, agent):
        return self.cli_cmd('tabadmin status -v', agent)

    def cli_cmd(self, command, agent, env=None, immediate=False):
        """ 1) Sends the command (a string)
            2) Waits for status/completion.  Saves the body from the status.
            3) Sends cleanup.
            4) Returns body from the status.
        """

        body = self._send_cli(command, agent, env=env, immediate=immediate)

        if body.has_key('error'):
            return body

        if not body.has_key('run-status'):
            return self.error("_send_cli (%s) body response missing 'run-status': %s" % \
                (command, str(body)))

        # It is possible for the command to finish immediately.
        if body['run-status'] == 'finished':
            return body

        cli_body = self._get_cli_status(body['xid'], agent, command)

        if not 'stdout' in cli_body:
            self.log.error(\
                "check status of cli failed - missing 'stdout' in reply" + \
                                    "for command '%s': %s", command, cli_body)
            if not 'error' in cli_body:
                cli_body['error'] = \
                    "Missing 'stdout' in agent reply for command '%s': %s" % \
                    (command, cli_body)

        cleanup_body = self._send_cleanup(body['xid'], agent, command)

        if cli_body.has_key("error"):
            return cli_body

        if cleanup_body.has_key('error'):
            return cleanup_body

        return cli_body

    def _send_cli(self, cli_command, agent, env=None, immediate=False):
        """Send a "cli" command to an Agent.
            Returns a body with the results.
            Called without the connection lock."""

        self.log.debug("_send_cli")

        aconn = agent.connection
        aconn.lock()

        req = CliStartRequest(cli_command, env=env, immediate=immediate)

        headers = {"Content-Type": "application/json"}
        uri = self.CLI_URI

        displayname = agent.displayname and agent.displayname or agent.uuid
        self.log.debug("about to send the cli command to '%s', type '%s' xid: %d, command: %s",
                displayname, agent.agent_type, req.xid, cli_command)
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
                               cli_command, res.status, res.reason, body_json)
                reason = "Command sent to agent failed. Error: " + res.reason
                self.remove_agent(agent, reason)
                return self.httperror(res, method="POST",
                                      displayname=agent.displayname,
                                      uri=uri, body=body_json)

        except (httplib.HTTPException, EnvironmentError) as e:
            self.log.error(\
                "_send_cli: command '%s' failed with httplib.HTTPException: %s",
                                                        cli_command, str(e))
            self.remove_agent(agent, EventControl.AGENT_COMM_LOST) # bad agent
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

        self.log.debug('about to send the cleanup command, xid %d',  xid)
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
                alert = "Command to agent failed with status: " + \
                                                            str(res.status)
                self.remove_agent(agent, alert)
                return self.httperror(res, method="POST",
                                      displayname=agent.displayname,
                                      uri=uri, body=body_json)

            self.log.debug("headers: " + str(res.getheaders()))
            self.log.debug("_send_cleanup reading...")

        except (httplib.HTTPException, EnvironmentError) as e:
            # bad agent
            self.log.error("_send_cleanup: POST %s for '%s' failed with: %s",
                           uri, orig_cli_command, str(e))
            self.remove_agent(agent, "Command to agent failed. " \
                                  + "Error: " + str(e))
            return self.error("'%s' failed for command '%s' with: %s" % \
                                  (uri, orig_cli_command, str(e)))
        finally:
            # Must call aconn.unlock() even after self.remove_agent(),
            # since another thread may waiting on the lock.
            aconn.unlock()
            self.log.debug("_send_cleanup unlocked")

        self.log.debug("done reading.")
        body = json.loads(body_json)
        if body == None:
            return self.error("POST /%s getresponse returned null body" % uri)
        return body

    def copy_cmd(self, source_path, dest_name, target_dir):
        """Sends a phttp command and checks the status.
           copy source-displayname:/path/to/file dest-displayname dir
                       <source_path>          <dest-displayname>
           generates:
               phttp.exe GET https://primary-ip:192.168.1.1/file dir/
           and sends it as a cli command to agent:
                dest-displayname
           Returns the body dictionary from the status."""

        if source_path.find(':') == -1:
            return self.error("Missing ':' in source path: %s" % source_path)

        (source_displayname, source_path) = source_path.split(':',1)

        if len(source_displayname) == 0 or len(source_path) == 0:
            return self.error("[ERROR] Invalid source specification.")

        agents = self.agentmanager.all_agents()
        src = dst = None

        for key in agents.keys():
            self.agentmanager.lock()
            if not agents.has_key(key):
                self.log.info(\
                    "copy_cmd: agent with uuid '%s' is now gone and " + \
                                                    "won't be checked.", key)
                self.agentmanager.unlock()
                continue
            agent = agents[key]
            self.agentmanager.unlock()

            if agent.displayname == source_displayname:
                src = agent
            if agent.displayname == dest_name:
                dst = agent

        msg = ""
        # fixme: make sure the source isn't the same as the dest
        if not src:
            msg = "No connected source agent with displayname: %s." % \
              source_displayname
        if not dst:
            msg += "No connected destination agent with displayname: %s." % \
              dest_name

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
                data = agent.todict(pretty=True)
                data['error'] = fw_body['error']
                data['info'] = "Port " + str(src.listen_port)
                self.event_control.gen(EventControl.FIREWALL_OPEN_FAILED, data)
                return fw_body

        source_ip = src.ip_address

       # Make sure the target directory on the target agent exists.
        try:
            dst.filemanager.mkdirs(target_dir)
        except (IOError, ValueError) as e:
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
            self.log.err("Source agent not found!  agentid: %d", src.agentid)
            return self.error("Source agent not found in agent table: %d " % \
                                                                src.agentid)

        env = {u'BASIC_USERNAME': entry.username,
               u'BASIC_PASSWORD': entry.password}

        self.log.debug("agent username: %s, password: %s", entry.username,
                                                            entry.password)
        # Send command to destination agent
        copy_body = self.cli_cmd(command, dst, env=env)
        return copy_body

    def restore_cmd(self, primary_agent, backup_full_path, orig_state,
                    userid=None):
        """Do a tabadmin restore for the backup_full_path.
           The backup_full_path may be in cloud storage, or a volume
           on some agent.

           Returns a body with the results/status.
        """

        backup_entry = self.backup.find_by_name(backup_full_path)
        if not backup_entry:
            self.stateman.update(orig_state)
            return self.error("Backup name not found: %s" % backup_full_path)

        # Get the gcs, s3 or vol entry
        if backup_entry.gcsid:
            source_type = StorageConfig.GCS
            source_entry = self.gcs.get_by_gcsid(backup_entry.gcsid)
            cloud_cmd = self.gcs_cmd
        elif backup_entry.s3id:
            source_type = StorageConfig.S3
            source_entry = self.s3.get_by_s3id(backup_entry.s3id)
            cloud_cmd = self.s3_cmd
        elif backup_entry.agentid:
            source_type = StorageConfig.VOL
            # fixme: support linux
            vol_name = backup_entry.name.split(':')[0]
            source_entry = AgentVolumesEntry.get_vol_entry_by_agentid_vol_name(
                                backup_entry.agentid, vol_name)

            if not source_entry:
                return self.error(
                    ("restore_cmd: vol entry not found for backup " + \
                     "agentid %d, name %s") % \
                     (backup_entry.agentid, vol_name))

            source_agent = Agent.get_by_id(source_entry.agentid)
            if not source_agent:
                return self.error(
                    "restore_cmd: No such agentid %d referenced by " + \
                    "agentid %d and name %s in backupid %d" % \
                        (source_entry.agentid, backup_entry.volid,
                                                    backup_entry.backupid))
        else:
            return self.error(
                "restore_cmd: Backup has no gcs/s3/agentid for backup %s" % \
                                                        backup_full_path)

        # The tableau backup file to use when calling the
        # 'tabadmin restore <backup-file>' command.
        # It will be this in all cases except if the backup
        # file is on the primary but on a different volume than
        # the palette install.

        # Keep track of whether or not a backup was copied to the primary
        # for the restore.  If so, we'll need to delete the
        # file after the restore finishes or an error.

        backup_copied = False
        if source_type in (StorageConfig.GCS, StorageConfig.S3):
            # The backup is cloud storage: s3 or gcs
            self.log.debug(\
                "restore: Sending %s command to primary '%s' to GET '%s'", \
                   source_type, primary_agent.displayname, backup_full_path)

            # Cloud storage doesn't support directories.  The
            # backup_full_path on the cloud storage was only the filename.
            # We change backup_full_path to be the full path of where
            # we want to copy the file to.
            backup_full_path = primary_agent.path.join(
                    self.primary_backup_dir(primary_agent),
                    primary_agent.path.basename(backup_full_path))

            body = cloud_cmd(primary_agent, "GET", source_entry,
                             backup_full_path)
            if 'error' in body:
                fmt = "restore: %s named '%s' GET backup file '%s' " + \
                    "failed.  Error: %s"
                self.log.debug(fmt,
                           source_type,
                           source_entry.name,
                           backup_full_path,
                           body['error'])
                self.stateman.update(orig_state)
                return body

            backup_copied = True
        elif source_type == StorageConfig.VOL:
            # First copy backup file to the primary if it isn't there yet.
            # Backup is on a disk volume (not cloud storage).
            # It could be on the main primary volume, or another
            # primary volume or a volume on an agent.

            if source_agent.displayname != primary_agent.displayname:
                # The file isn't on the Primary agent or cloud storage.
                # We need to copy the file to the Primary.
                # copy_cmd arguments:
                #   source:    source-agent-name:VOL/tableau-backups/filename
                #   dest_name: dest-agent-displayname
                #   dest_dir:  palette-primary-data-path/tableau-backups
                # source is something like:
                #               "C/tableau-backups/20140531_153629.tsbak"
                # with only the "tableau-backup/20140531_153629.tsbak"
                # last part.

                # Remove the agent's 'data-dir' portion of the beginning
                # of the source_path.
                # For example, given:
                #   \ProgramData\Palette\Data\tableau-backups\2014.gone.tsbak
                # and a source_entry path of:
                #   \ProgramData\Palette\Data
                # end up with:
                #   \tableau-backups\2014.gone.tsbak

                (backup_vol, backup_path) = backup_full_path.split(':',1)

                common = os.path.commonprefix([backup_path, source_entry.path])

                if common:
                    # Chop off the leading common part in routes.txt
                    backup_path = backup_path[len(common):]

                copy_source = "%s:%s%s" % \
                              (source_agent.displayname, source_entry.name,
                              backup_path)
                            
                self.log.debug(\
                    "restore: Sending copy command to '%s' to get: %s", \
                                       source_agent.displayname, copy_source)

                backup_dir = self.primary_backup_dir(primary_agent)

                body = self.copy_cmd(copy_source, primary_agent.displayname,
                                     backup_dir)

                if body.has_key("error"):
                    fmt = "restore: copy backup file '%s' " + \
                          "from '%s' to directory '%s' failed. " +\
                          "Error was: %s"
                    self.log.debug(fmt,
                                   copy_source,
                                   source_agent.displayname,
                                   backup_dir,
                                   body['error'])
                    self.stateman.update(orig_state)
                    return body

                # This is the filename to use for 'tabadmin restore'
                # now that it is copied to the primary.
                backup_full_path = primary_agent.path.join(
                    self.primary_backup_dir(primary_agent), 
                    primary_agent.path.basename(backup_full_path))

                backup_copied = True

        # The restore file is now on the Primary Agent.
        data = primary_agent.todict(pretty=True)
        self.event_control.gen(EventControl.RESTORE_STARTED,
                               data, userid=userid)

        reported_status = self.statusmon.get_reported_status()

        if reported_status == TableauProcess.STATUS_RUNNING:
            # Restore can run only when tableau is stopped.
            self.stateman.update(StateManager.STATE_STOPPING_RESTORE)
            self.log.debug("------------Stopping Tableau for restore-------------")
            stop_body = self.cli_cmd("tabadmin stop", primary_agent)
            if stop_body.has_key('error'):
                self.log.info("Restore: tabadmin stop failed")
                if backup_copied:
                    # If the file was copied to the Primary, delete
                    # the temporary backup file we copied to the Primary.
                    self.delete_file(primary_agent, backup_full_path)
                self.stateman.update(orig_state)
                return stop_body

            data = primary_agent.todict(pretty=True)
            self.event_control.gen(EventControl.STATE_STOPPED, data)

        # 'tabadmin restore ...' starts tableau as part of the
        # restore procedure.
        # fixme: Maybe the maintenance web server wasn't running?
        # We currently don't keep track, but assume the maintenance
        # web server may be running if Tableau is stopped.
        maint_msg = ""
        if orig_state == StateManager.STATE_STOPPED:
            maint_body = self.maint("stop", agent=primary_agent)
            if maint_body.has_key("error"):
                self.log.info("Restore: maint stop failed: " + maint_body['error'])
                # continue on, not a fatal error...
                maint_msg = "Restore: maint stop failed.  Error was: %s" \
                                                    % maint_body['error']

        self.stateman.update(StateManager.STATE_STARTING_RESTORE)
        try:
            cmd = 'tabadmin restore \\\"%s\\\"' % backup_full_path
            self.log.debug("restore sending command: %s", cmd)
            restore_body = self.cli_cmd(cmd, primary_agent)
        except httplib.HTTPException, e:
            restore_body = { "error": "HTTP Exception: " + str(e) }

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

        if backup_copied:
            # If the file was copied to the Primary, delete
            # the temporary backup file we copied to the Primary.
            delete_body = self.delete_file(primary_agent, backup_full_path)
            if 'error' in delete_body:
                info += '\n' + delete_body['error']

        if restore_success:
            self.stateman.update(StateManager.STATE_STARTED)
            data = primary_agent.todict(pretty=True)
            self.event_control.gen(EventControl.STATE_STARTED, data)
        else:
            # On a successful restore, tableau starts itself.
            # fixme: eventually control when tableau is started and
            # stopped, rather than have tableau automatically start
            # during the restore.  (Tableau does not support this currently.)
            self.log.info("Restore: starting tableau after failed restore.")
            start_body = self.cli_cmd("tabadmin start", primary_agent)
            if 'error' in start_body:
                self.log.info(\
                    "Restore: 'tabadmin start' failed after failed restore.")
                msg = "Restore: 'tabadmin start' failed after failed restore."
                msg += " Error was: %s" % start_body['error']
                info += "\n" + msg

                 # The "tableau start" failed.  Go back to the "STOPPED" state.
                self.stateman.update(StateManager.STATE_STOPPED)
            else:
                # The "tableau start" succeeded
                self.stateman.update(StateManager.STATE_STARTED)
                data = primary_agent.todict(pretty=True)
                self.event_control.gen(EventControl.STATE_STARTED, data)

        if 'info':
            restore_body['info'] = info.strip()

        return restore_body

    def delete_file(self, agent, source_fullpathname):
        """Delete a file, check the error, and return the body result."""
        self.log.debug("Removing file '%s'", source_fullpathname)
        cmd = 'CMD /C DEL \\\"%s\\\"' % source_fullpathname
        remove_body = self.cli_cmd(cmd, agent)
        if remove_body.has_key('error'):
            self.log.info('DEL of "%s" failed.', source_fullpathname)
            # fixme: report somewhere the DEL failed.
        return remove_body

    def _get_cli_status(self, xid, agent, orig_cli_command):
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

        uri = self.CLI_URI + "?xid=" + str(xid)
        headers = {"Content-Type": "application/json"}

        aconn = agent.connection
        while True:
            self.log.debug("about to get status of cli command '%s', xid %d",
                           orig_cli_command, xid)

            # If the agent is initializing, then "agent_connected"
            # will not know about it yet.
            if not aconn.initting and \
                    not self.agentmanager.agent_connected(agent.uuid):
                self.log.warning("Agent '%s' (type: '%s', uuid %s) " + \
                        "disconnected before finishing: %s",
                           agent.displayname, agent.agent_type, agent.uuid, uri)
                return self.error(("Agent '%s' (type: '%s', uuid %s) " + \
                    "disconnected before finishing: %s") %
                        (agent.displayname, agent.agent_type, agent.uuid, uri))

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
            except httplib.HTTPException, e:
                    self.remove_agent(agent,
                        "HTTP communication failure with agent: " + \
                                                        str(e))    # bad agent
                    return self.error("GET %s failed with HTTPException: %s" \
                                                                % (uri, str(e)))
            except EnvironmentError, e:
                    self.remove_agent(agent, "Communication failure with " + \
                            "agent. Unexpected error: " + str(e))    # bad agent
                    return self.error("GET %s failed with: %s" % (uri, str(e)))

    def odbc_ok(self):
        """Reports back True if odbc commands can be run now to
           the postgres database.  odbc commands should be not sent
           in these cases:
            * When the tableau is stopped, since the postgres is also
              stopped when tableau is stopped.
            * When in "UPGRADE" mode.
        """
        main_state = self.stateman.get_state()
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
        main_state = self.stateman.get_state()
        if main_state == StateManager.STATE_UPGRADING:
            return True
        else:
            return False

    def get_pinfo(self, agent, update_agent=False):
        if self.upgrading():
            self.log.info("get_pinfo: Failing due to UPGRADING")
            raise exc.InvalidStateError("Cannot run command while UPGRADING")

        aconn = agent.connection
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
        except ValueError, e:
            self.log.error("Bad json from pinfo. Error: %s, json: %s", \
                               str(e), json_str)
            raise IOError("Bad json from pinfo.  Error: %s, json: %s" % \
                (str(e), json_str))
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
                                    "displayname.  uuid: %s",  agent.uuid)
                raise IOError("get_pinfo: Could not update agent: unknown " + \
                        "displayname.  uuid: %s" % agent.uuid)

        return pinfo

    def license(self, agent):
        if self.upgrading():
            self.log.info("get_pinfo: Failing due to UPGRADING")
            return {"error": "Cannot run command while UPGRADING"}

        body = self.cli_cmd('tabadmin license', agent)

        if not 'exit-status' in body or body['exit-status'] != 0:
            return body
        if not 'stdout' in body:
            return body

        session = meta.Session()

        output = body['stdout']
        d = LicenseEntry.parse(output)
        entry = LicenseEntry.get(agentid=agent.agentid, **d)
        session.commit()

        if entry.invalid():
            if not entry.notified:
                # Generate an event
                data = agent.todict(pretty=True)
                data['error'] = "interactors: %s, viewers: %s" % \
                    (entry.interactors, entry.viewers)
                self.event_control.gen(EventControl.LICENSE_INVALID, data)
                entry.notified = True
                session.commit()
            return self.error(\
                "License invalid on '%s': interactors: %s, viewers: %s" % \
                    (agent.displayname, entry.interactors, entry.viewers))

        return d

    def yml(self, agent):
        path = agent.path.join(agent.tableau_data_dir, "data", "tabsvc",
                               "config", "workgroup.yml")
        yml = agent.filemanager.get(path)
        body = self.agentmanager.update_agent_yml(agent.agentid, yml)
        return body

    def sync_cmd(self, agent):
        """sync/copy tables from tableau to here."""

        if not self.odbc_ok():
            main_state = self.stateman.get_state()
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
            if error_msg: error_msg += ", "
            error_msg += "Project sync failure: " + body['error']
        else:
            sync_dict['projects'] = body['count']

        body = DataConnection.sync(agent)
        if 'error' in body:
            if error_msg: error_msg += ", "
            error_msg += "DataConnection sync failure: " + body['error']
        else:
            sync_dict['data-connections'] = body['count']

        if error_msg:
            sync_dict['error'] = error_msg

        return sync_dict

    def maint(self, action, port=-1, agent=None, send_alert=True):
        if action not in ("start", "stop"):
            self.log.error("Invalid maint action: %s", action)
            return self.error("Bad maint action: %s" % action)

        manager = self.agentmanager

        # FIXME: Tie agent to domain
        if not agent:
            agent = manager.agent_by_type(AgentManager.AGENT_TYPE_PRIMARY)
            if not agent:
                return self.error("maint: no primary agent is known.")

            elif not agent.connection:
                return self.error("maint: no primary agent is connected.")

        send_body = {"action": action}
        if port > 0:
            send_body["port"] = port

        body = self.send_immediate(agent, "POST", "/maint", send_body)

        if body.has_key("error"):
            data = agent.todict(pretty=True)
            data['error'] = body['error']
            if action == "start":
                self.event_control.gen(EventControl.MAINT_START_FAILED, data)
            else:
                self.event_control.gen(EventControl.MAINT_STOP_FAILED, data)
            return body

        if not send_alert:
            return body

        data = agent.todict(pretty=True)
        if action == 'start':
            self.event_control.gen(EventControl.MAINT_ONLINE, data)
        else:
            self.event_control.gen(EventControl.MAINT_OFFLINE, data)

        return body

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

        self.log.debug(\
            "about to send an immediate command to '%s', type '%s', " + \
                "method '%s', uri '%s', body '%s'",
                    agent.displayname, agent.agent_type, method, uri, send_body)

        aconn = agent.connection
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
        except (httplib.HTTPException, EnvironmentError) as e:
            self.log.error("Agent send_immediate command %s %s failed: %s",
                                        method, uri, str(e))    # bad agent
            self.remove_agent(agent, \
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

        self.agentmanager.set_displayname(aconn, uuid, displayname)

    def ziplogs_cmd(self, agent, target=None):
        """Run tabadmin ziplogs'."""

        aconn = agent.connection
        ziplog_name = time.strftime("%Y%m%d_%H%M%S") + ".logs.zip"
        path = self.backup.palette_primary_data_loc_path(agent)
        ziplog_path = agent.path.join(path, self.LOG_DIR)

        #self.event_control.gen(EventControl.ZIPLOGS_STARTED,....
        cmd = 'tabadmin ziplogs -l -n -a \\\"%s\\\"' % ziplog_path
        body = self.cli_cmd(cmd, agent)
        body[u'info'] = u'tabadmin ziplogs -l -n -a ziplog_name'

        if 'error' in body:
            data = agent.todict(pretty=True)
            self.event_control.gen(EventControl.ZIPLOGS_FAILED,
                                   dict(body.items() + data.items()))
        else:
            #self.event_control.gen(EventControl.ZIPLOGS_FINISHED,....

        return body

    def cleanup_cmd(self, agent, target=None):
        """Run tabadmin cleanup'."""

        aconn = agent.connection

        #self.event_control.gen(EventControl.CLEANUP_STARTED,....
        body = self.cli_cmd('tabadmin cleanup', agent)
        body[u'info'] = u'tabadmin cleanup'
        # 'tabadmin cleanup' returns an exit status of 1 but sends
        # the error to stdout instead of stderr.
        #
        if 'exit-status' in body and body['exit-status'] != 0 and \
                            'stderr' in body and not body['stderr']:
            if 'error' in body and not body['error'] or \
                                                not 'error' in body:
                if 'stdout' in body:
                    body['error'] = body['stdout']

        if 'error' in body:
            data = agent.todict(pretty=True)
            self.event_control.gen(EventControl.CLEANUP_FAILED,
                                   dict(body.items() + data.items()))
        else:
            self.event_control.gen(EventControl.CLEANUP_FINISHED,....
        return body

    def error(self, msg, return_dict={}):
        """Returns error dictionary in standard format.  If passed
           a return_dict, then adds to it, otherwise a new return_dict
           is created."""

        return_dict['error'] = unicode(msg)
        return return_dict

    def httperror(self, res, error='HTTP failure',
                  displayname=None, method='GET', uri=None, body=None):
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
        if displayname:
            d['agent'] = displayname
        return d;

    def init_new_agent(self, agent):
        """Agent-related configuration on agent connect.
            Args:
                aconn: agent connection
            Returns:
                pinfo dictionary:  The agent responded correctly.
                False:  The agent responded incorrectly.
        """

        TABLEAU_INSTALL_DIR="tableau-install-dir"
        YML_CONFIG_FILE_PART=agent.path.join("data", "tabsvc",
                                             "config", "workgroup.yml")

        aconn = agent.connection

        pinfo = self.get_pinfo(agent, update_agent=False)

        self.log.debug("info returned from %s: %s", aconn.displayname, str(pinfo))
        # Set the type of THIS agent.
        if TABLEAU_INSTALL_DIR in pinfo:
            # FIXME: don't duplicate the data
            agent.agent_type = aconn.agent_type \
                = AgentManager.AGENT_TYPE_PRIMARY

            if pinfo[TABLEAU_INSTALL_DIR].find(':') == -1:
                self.log.error("agent %s is missing ':': %s for %s",
                               aconn.displayname, TABLEAU_INSTALL_DIR,
                               agent.tableau_install_dir)
                return False
        else:
            if self.agentmanager.is_tableau_worker(agent.ip_address):
                agent.agent_type = aconn.agent_type = \
                                    AgentManager.AGENT_TYPE_WORKER
            else:
                agent.agent_type = aconn.agent_type = \
                                    AgentManager.AGENT_TYPE_ARCHIVE

        # This saves directory-related info from pinfo: it
        # does not save the volume info since we may not
        # know the displayname yet and the displayname is
        # needed for a disk-usage event report.
        self.agentmanager.update_agent_pinfo_dirs(agent, pinfo)

        # Note: Don't call this before update_agent_pinfo_dirs()
        # (needed for agent.tableau_data_dir).
        if agent.agent_type == AgentManager.AGENT_TYPE_PRIMARY:
            self.yml(agent)     # raises an exception on fail
            if self.odbc_ok():
                if failed(self.auth.load(agent)):
                    raise IOError("initial auth load failed")
                self.sync_cmd(agent)  # ok to fail if not IOError
                self.extract.load(agent)    # ok to fail if ot IOError

        if agent.iswin:
            self.firewall_manager.do_firewall_ports(agent)

        self.clean_xid_dirs(agent)
        self.config_servers(agent)

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
            #agent.filemanager.delete(full_path)

    def config_servers(self, agent):
        """Configure the maintenance and archive servers."""
        if agent.agent_type == AgentManager.AGENT_TYPE_PRIMARY:
            # Put into a known state
            body = self.maint("stop", agent=agent, send_alert=False)
            if body.has_key("error"):
                data = agent.todict(pretty=True)
                self.event_control.gen(EventControl.MAINT_STOP_FAILED,
                                       dict(body.items() + data.items()))

        body = self.archive(agent, "stop")
        if body.has_key("error"):
            data = agent.todict(pretty=True)
            self.event_control.gen(EventControl.ARCHIVE_STOP_FAILED,
                                   dict(body.items() + data.items()))
        # Get ready.
        body = self.archive(agent, "start")
        if body.has_key("error"):
            data = agent.todict(pretty=True)
            self.event_control.gen(EventControl.ARCHIVE_START_FAILED,
                                   dict(body.items() + data.items()))

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
        self.flush(self)

    def flush(self):
        self.writeln(self.buf)
        self.buf = ''

def main():
    import argparse
    import logger

    parser = argparse.ArgumentParser(description='Palette Controller')
    parser.add_argument('config', nargs='?', default=None)
    parser.add_argument('--nostatus', action='store_true', default=False)
    parser.add_argument('--noping', action='store_true', default=False)
    parser.add_argument('--nosched', action='store_true', default=False)
    args = parser.parse_args()

    config = Config(args.config)
    host = config.get('controller', 'host', default='localhost');
    port = config.getint('controller', 'port', default=9000);
    agent_port = config.getint('controller', 'agent_port', default=22);

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
                                               expire_on_commit=False))

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

    server.event = EventManager(server.environment.envid)

    server.system = SystemManager(server.environment.envid)
    SystemManager.populate()

    StateControl.populate()

    server.auth = AuthManager(server)
    server.extract = ExtractManager(server)

    Role.populate()
    UserProfile.populate()

    # Must be done after auth, since it use the users table.
    server.alert_email = AlertEmail(server)

    EventControl.populate()
    server.event_control = EventControlManager(server)

    workbook_manager = WorkbookManager(server.environment.envid)

    server.backup = BackupManager(server.environment.envid)

    server.gcs = GCS(server.environment.envid)
    server.s3 = S3(server.environment.envid)

    server.firewall_manager = FirewallManager(server)

    server.stateman = StateManager(server)

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
        os._exit(1)
