#!/usr/bin/env python

import sys
import os
import SocketServer as socketserver
import socket

import json
import time

import exc
from request import *

import httplib
import inspect
import ntpath

import sqlalchemy
from sqlalchemy.orm import sessionmaker, scoped_session
from akiri.framework.ext.sqlalchemy import meta

from agentmanager import AgentManager
from agent import Agent
from agentinfo import AgentVolumesEntry
from auth import AuthManager
from backup import BackupManager
from diskcheck import DiskCheck
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
from extracts import ExtractsEntry
from workbooks import WorkbookEntry, WorkbookManager
from s3 import S3
from sched import Sched
from clihandler import CliHandler
from version import VERSION

class Controller(socketserver.ThreadingMixIn, socketserver.TCPServer):

    LOGGER_NAME = "main"
    allow_reuse_address = True

    PHTTP_BIN = "phttp.exe"
    PINFO_BIN = "pinfo.exe"
    PS3_BIN = "ps3.exe"
    CLI_URI = "/cli"

    def backup_cmd(self, aconn, target=None, volume_name=None):
        """Perform a backup - not including any necessary migration."""

        if volume_name and not target:
            return self.error(\
                "volume_name can be specified only when target is specified.")

        # Disk space check.
        dcheck = DiskCheck(self, aconn, target, volume_name)
        if not dcheck.set_locs():
            return self.error(dcheck.error_msg)

        if dcheck.target_conn:
            self.log.debug("Backup will copy to target '%s', target_dir '%s'",
                        dcheck.target_conn.displayname, dcheck.target_dir)
        else:
            self.log.debug("Backup will stay on the primary.")

        # Example name: 20140127_162225.tsbak
        backup_name = time.strftime("%Y%m%d_%H%M%S") + ".tsbak"

        # Get the vol + dir to use for the backup command to tabadmin.
        backup_dir = self.backup.primary_data_loc_path()
        if not backup_dir:
            return self.error("Couldn't find the primary_data_loc in " + \
                        "the agent_volumes table for the primary agent.")

        backup_path = ntpath.join(backup_dir, backup_name)

        backup_vol = backup_path.split(':')[0]
        # e.g.: c:\\Program\ Files\ (x86)\\Palette\\Data\\2014Jan27_162225.tsbak
        cmd = 'tabadmin backup \\\"%s\\\"' % backup_path
        body = self.cli_cmd(cmd, aconn)
        if body.has_key('error'):
            return body

        body['info'] = ""

        backup_vol_entry = None
        # If the target is not the primary, copy the backup to the target.
        if dcheck.target_conn:
            backup_vol_entry = dcheck.vol_entry
            # Copy the backup to a non-primary agent
            source_path = "%s:%s/%s" % (aconn.displayname, backup_vol,
                                                                backup_name)
            copy_body = self.copy_cmd(source_path,
                        dcheck.target_conn.displayname, dcheck.target_dir)

            if copy_body.has_key('error'):
                msg = (u"Copy of backup file '%s' to agent '%s:%s' failed. "+\
                    "Will leave the backup file on the primary agent. " + \
                    "Error was: %s") \
                    % (backup_name, dcheck.target_conn.displayname, 
                                    dcheck.target_dir, copy_body['error'])
                self.log.info(msg)
                body['info'] += msg
                # Something was wrong with the copy to the non-primary agent.
                #  Leave the backup on the primary after all.
                backup_vol_entry = None
            else:
                # The copy succeeded.
                # Remove the backup file from the primary
                remove_body = self.delete_file(aconn, backup_path)

                body['info'] += \
                    "Backup file copied to '%s'" % \
                                        dcheck.target_conn.displayname

                # Check if the DEL worked.
                if remove_body.has_key('error'):
                    body['info'] += \
                        ("\nDEL of backup file failed after copy. "+\
                            "file: '%s'. Error was: %s") \
                            % (backup_path, remove_body['error'])

        # Save backup filename and volid to the db.
        if backup_vol_entry:
            # Backup was copied to a target
            self.backup.add(backup_name, backup_vol_entry.volid)
        else:
            # Backup remains on the primary.  Dig out the volid for it.
            try:
                vol_entry = meta.Session.query(AgentVolumesEntry).\
                    filter(AgentVolumesEntry.agentid == aconn.agentid).\
                    filter(AgentVolumesEntry.primary_data_loc == True).\
                    one()
            except sqlalchemy.orm.exc.NoResultFound:
                body['info'] += "no primary data location volume found! " + \
                        "backup information cannot be saved to the database."
                return body

            self.backup.add(backup_name, vol_entry.volid)

        return body

    def backupdel_cmd(self, backup):
        """Delete a Tableau backup."""

        # FIXME: tie backup to domain

        result = self.backup.find_by_name(backup)
        if not result:
            return self.error("no backup found with name: %s" % (backup))

        (backupid, volid, vol_name, vol_path, agentid) = result[0]

        agent = Agent.get_agentstatusentry_by_volid(volid)

        aconn = self.agentmanager.agent_conn_by_uuid(agent.uuid)
        if not aconn:
            return self.error("agent not connected: displayname=%s uuid=%s" % \
              (agent.displayname, agent.uuid))

        backup_path = ntpath.join(vol_name + ":", vol_path, backup)
        self.log.debug("backupdel_cmd: Deleting path '%s' on agent '%s'",
                                            backup_path, agent.displayname)

        body = self.delete_file(aconn, backup_path)
        if not body.has_key('error'):
            try:
                self.backup.remove(backupid)
            except sqlalchemy.orm.exc.NoResultFound:
                return self.error("backup not found name=%s agent=%s" % \
              (backup, agent.displayname))

        return body

    def status_cmd(self, aconn):
        return self.cli_cmd('tabadmin status -v', aconn)

    def cli_cmd(self, command, aconn, env=None, immediate=False):
        """ 1) Sends the command (a string)
            2) Waits for status/completion.  Saves the body from the status.
            3) Sends cleanup.
            4) Returns body from the status.
        """

        body = self._send_cli(command, aconn, env=env, immediate=immediate)

        if body.has_key('error'):
            return body

        if not body.has_key('run-status'):
            return self.error("_send_cli (%s) body response missing 'run-status: '" % \
                (command, str(e)))

        # It is possible for the command to finish immediately.
        if body['run-status'] == 'finished':
            return body

        cli_body = self._get_cli_status(body['xid'], aconn, command)

        if not cli_body.has_key("stdout"):
            self.log.error(\
                "check status of cli failed - missing 'stdout' in reply",
                                                                    cli_body)
            return self.error(\
                "Missing 'stdout' in agent reply for command '%s'" % command,
                                                                    cli_body)

        cleanup_body = self._send_cleanup(body['xid'], aconn, command)

        if cli_body.has_key("error"):
            return cli_body

        if cleanup_body.has_key('error'):
            return cleanup_body

        return cli_body

    def _send_cli(self, cli_command, aconn, env=None, immediate=False):
        """Send a "cli" command to an Agent.
            Returns a body with the results.
            Called without the connection lock."""

        self.log.debug("_send_cli")

        aconn.lock()

        req = CliStartRequest(cli_command, env=env, immediate=immediate)

        headers = {"Content-Type": "application/json"}

        displayname = aconn.displayname and aconn.displayname or aconn.uuid
        self.log.debug("about to send the cli command to '%s', type '%s' xid: %d, command: %s",
                displayname, aconn.agent_type, req.xid, cli_command)
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
                reason = "Command sent to agent failed. Error: " + str(e)
                self.remove_agent(aconn, reason)
                return self.httperror(aconn, res, method="POST",
                                      agent=aconn.displayname,
                                      uri=uri, body=body_json)

        except (httplib.HTTPException, EnvironmentError) as e:
            self.log.error(\
                "_send_cli: command '%s' failed with httplib.HTTPException: %s",
                                                        cli_command, str(e))
            self.remove_agent(aconn, EventControl.AGENT_COMM_LOST) # bad agent
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

    def _send_cleanup(self, xid, aconn, orig_cli_command):
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
                self.remove_agent(aconn, alert)
                return self.httperror(aconn, res, method="POST",
                                      agent=aconn.displayname,
                                      uri=uri, body=body_json)

            self.log.debug("headers: " + str(res.getheaders()))
            self.log.debug("_send_cleanup reading...")

        except (httplib.HTTPException, EnvironmentError) as e:
            # bad agent
            self.log.error("_send_cleanup: POST %s for '%s' failed with: %s",
                           uri, orig_cli_command, str(e))
            self.remove_agent(aconn, "Command to agent failed. " \
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

    def copy_cmd(self, source_path, dest_name, target_dir=None):
        """Sends a phttp command and checks the status.
           copy source-displayname:/path/to/file dest-displayname
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

        # Enable the firewall port on the source host.
        self.log.debug("Enabling firewall port %d on src host '%s'", \
                                    src.auth['listen-port'], src.displayname)
        fw_body = src.firewall.enable(src.auth['listen-port'])
        if fw_body.has_key("error"):
            self.log.error(\
                "firewall enable port %d on src host %s failed with: %s",
                        src.auth['listen-port'], src.displayname, 
                                                        fw_body['error'])
            return fw_body

        source_ip = src.auth['ip-address']

        if not target_dir:
            target_dir = self.backup.primary_data_loc_path()
            if not target_dir:
                return self.error("copy_cmd: Couldn't find the " + \
                        "primary_data_loc in the agent_volumes table " + \
                        "for the primary agent.")

        command = '%s GET "https://%s:%s/%s" "%s"' % \
            (Controller.PHTTP_BIN, source_ip, src.auth['listen-port'],
             source_path, target_dir)

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

    def restore_cmd(self, aconn, target, orig_state):
        """Do a tabadmin restore of the passed target, except
           the target is the format:
                source-displayname:pathname
            or
                pathname
            where pathname is:
                VOLUME/filename
            The "VOLUME" is looked up on the volume table and expanded.

            An example target:
                "Tableau Archive #201:C/20140602_174057.tsbak"

            If the target is not the Primary Agent, then the filename
            will be copied it to the Primary Agent before doing the
            tabadmin restore.

            Returns a body with the results/status.
        """

        # Note: In a restore context, 'target' is the source of the backup,
        #       while in a backup context 'target' is the destination.

        # Before we do anything, first do sanity checks.
        # Without a ':', assume the backup is still on the primary.
        parts = target.split(':')
        if len(parts) == 1:
            source_displayname = aconn.displayname
            source_spec = parts[0]
        elif len(parts) == 2:
            source_displayname = parts[0]   #.e.g "Tableau Archive #201"
            source_spec = parts[1]          # e.g. "C/20140531_153629.tsbak"
        else:
            self.stateman.update(orig_state)
            return self.error('Invalid target: ' + target)

        if os.path.isabs(source_spec):
            self.stateman.update(orig_state)
            return self.error(\
                "May not specify an absolute pathname or disk: " + \
                    source_spec)
        parts = source_spec.split('/')
        if len(parts) == 1:
            # FIXME
            return self.error( \
                "restore: Bad target spec:  Missing '/': " + source_spec)
        filename_only = parts[1] #  e.g. "20140531_153629.tsbak"

        # Get the vol + dir to use for the restore command to tabadmin.
        backup_dir = self.backup.primary_data_loc_path()
        if not backup_dir:
            return self.error("restore: Couldn't find the primary_data_loc " + \
                        "in the agent_volumes table for the primary agent.")

        local_fullpathname = ntpath.join(backup_dir, filename_only)

        # Check if the file is on the Primary Agent.
        if source_displayname != aconn.displayname:
            # The file isn't on the Primary agent:
            # We need to copy the file to the Primary.

            # copy_cmd arguments:
            #   source-agent-name:/filename
            #   dest-agent-displayname
            self.log.debug("restore: Sending copy command: %s, %s", \
                               target, aconn.displayname)
            # target is something like: "C/20140531_153629.tsbak"
            body = self.copy_cmd(target, aconn.displayname, backup_dir)

            if body.has_key("error"):
                fmt = "restore: copy backup file '%s' from '%s' failed. " +\
                    "Error was: %s"
                self.log.debug(fmt,
                               source_spec,
                               source_displayname,
                               body['error'])
                self.stateman.update(orig_state)
                return body

        # The restore file is now on the Primary Agent.
        self.event_control.gen(EventControl.RESTORE_STARTED, aconn.__dict__)

        reported_status = self.statusmon.get_reported_status()

        if reported_status == TableauProcess.STATUS_RUNNING:
            # Restore can run only when tableau is stopped.
            self.stateman.update(StateManager.STATE_STOPPING_RESTORE)
            log.debug("------------Stopping Tableau for restore-------------")
            stop_body = self.cli_cmd("tabadmin stop", aconn)
            if stop_body.has_key('error'):
                self.log.info("Restore: tabadmin stop failed")
                if source_displayname != aconn.displayname:
                    # If the file was copied to the Primary, delete
                    # the temporary backup file we copied to the Primary.
                    self.delete_file(aconn, local_fullpathname)
                self.stateman.update(orig_state)
                return stop_body

            self.event_control.gen(EventControl.STATE_STOPPED, aconn.__dict__)

        # 'tabadmin restore ...' starts tableau as part of the
        # restore procedure.
        # fixme: Maybe the maintenance web server wasn't running?
        maint_msg = ""
        maint_body = self.maint("stop", aconn=aconn)
        if maint_body.has_key("error"):
            self.log.info("Restore: maint stop failed: " + maint_body['error'])
            # continue on, not a fatal error...
            maint_msg = "Restore: maint stop failed.  Error was: %s" \
                                                    % maint_body['error']

        self.stateman.update(StateManager.STATE_STARTING_RESTORE)
        try:
            cmd = 'tabadmin restore \\\"%s\\\"' % local_fullpathname
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
            self.delete_file(aconn, local_fullpathname)

        if restore_success:
            self.stateman.update(StateManager.STATE_STARTED)
            self.event_control.gen(EventControl.STATE_STARTED, aconn.__dict__)
        else:
            # On a successful restore, tableau starts itself.
            # fixme: eventually control when tableau is started and
            # stopped, rather than have tableau automatically start
            # during the restore.  (Tableau does not support this currently.)
            self.log.info("Restore: starting tableau after failed restore.")
            start_body = self.cli_cmd("tabadmin start", aconn)
            if start_body.has_key('error'):
                self.log.info(\
                    "Restore: 'tabadmin start' failed after failed restore.")
                msg = "Restore: 'tabadmin start' failed after failed restore."
                msg += " Error was: %s" % start_body['error']
                if restore_body.has_key('info'):
                    restore_body['info'] += "\n" + msg
                else:
                    restore_body['info'] = msg

                 # The "tableau start" failed.  Go back to the "STOPPED" state.
                self.stateman.update(StateManager.STATE_STOPPED)
            else:
                # The "tableau start" succeeded
                self.stateman.update(StateManager.STATE_STARTED)
                self.event_control.gen( \
                    EventControl.STATE_STARTED, aconn.__dict__)

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

    def _get_cli_status(self, xid, aconn, orig_cli_command):
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

        while True:
            self.log.debug("about to get status of cli command '%s', xid %d",
                           orig_cli_command, xid)

            # If the agent is initializing, then "agent_connected"
            # will not know about it yet.
            # FIXME: use agent here instead of aconn.uuid
            if not aconn.initting and \
                    not self.agentmanager.agent_connected(aconn.uuid):
                self.log.warning("Agent '%s' (type: '%s', uuid %s) " + \
                        "disconnected before finishing: %s",
                           aconn.displayname, aconn.agent_type, aconn.uuid, uri)
                return self.error(("Agent '%s' (type: '%s', uuid %s) " + \
                    "disconnected before finishing: %s") %
                        (aconn.displayname, aconn.agent_type, aconn.uuid, uri))

            aconn.lock()
            self.log.debug("Sending GET " + uri)

            try:
                aconn.httpconn.request("GET", uri, None, headers)

                self.log.debug("Getting response from GET " +  uri)
                res = aconn.httpconn.getresponse()
                self.log.debug("status: " + str(res.status) + ' ' + \
                                                            str(res.reason))
                if res.status != httplib.OK:
                    self.remove_agent(aconn,
                                 EventControl.AGENT_RETURNED_INVALID_STATUS)
                    return self.httperror(res, agent=aconn.displayname, uri=uri)

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
                    self.remove_agent(aconn,
                                     EventControl.AGENT_RETURNED_INVALID_STATUS)
                    return self.error(\
                        "GET %s command reply was missing 'run-status'!  " + \
                        "Will not retry." % (uri), body)

                if body['run-status'] == 'finished':
                    # Make sure if the command failed, that the 'error'
                    # key is set.
                    if body['exit-status'] != 0:
                        if body.has_key('stderr'):
                            body['error'] = body['stderr']
                        else:
                            body['error'] = u"Failed with exit status: %d" % \
                                                            body['exit-status']
                    return body
                elif body['run-status'] == 'running':
                    time.sleep(self.cli_get_status_interval)
                    continue
                else:
                    self.remove_agent(aconn,
                        "Communication failure with agent:  " + \
                        "Unknown run-status returned from agent: %s" % \
                                            body['run-status'])    # bad agent
                    return self.error("Unknown run-status: %s.  Will not " + \
                                            "retry." % body['run-status'], body)
            except httplib.HTTPException, e:
                    self.remove_agent(aconn,
                        "HTTP communication failure with agent: " + \
                                                        str(e))    # bad agent
                    return self.error("GET %s failed with HTTPException: %s" \
                                                                % (uri, str(e)))
            except EnvironmentError, e:
                    self.remove_agent(aconn, "Communication failure with " + \
                            "agent. Unexpected error: " + str(e))    # bad agent
                    return self.error("GET %s failed with: %s" % (uri, str(e)))

    def info(self, agent):
        aconn = agent.connection
        body = self.cli_cmd(Controller.PINFO_BIN, aconn, immediate=True)
        # FIXME: add a function to test cli success (cli_success?)
        if not 'exit-status' in body or body['exit-status'] != 0:
            return body;
        json_str = body['stdout']
        try:
            pinfo = json.loads(json_str)
        except ValueError, e:
            self.log.error("Bad json from pinfo. Error: %s, json: %s", \
                               str(e), json_str)
            return body
        if pinfo is None:
            self.log.error("Bad pinfo output: %s", json_str)
            return body
        self.agentmanager.update_agent_pinfo(agent, pinfo)
        return body

    def license(self, agent):
        body = self.cli_cmd('tabadmin license', agent.connection)

        if not 'exit-status' in body or body['exit-status'] != 0:
            return body
        if not 'stdout' in body:
            return body

        output = body['stdout']
        d = LicenseEntry.parse(output)
        LicenseEntry.save(agentid=agent.agentid, **d)
        return d

    def yml(self, agent):
        path = ntpath.join(agent.tableau_data_dir, "data", "tabsvc",
                           "config", "workgroup.yml")
        try:
            yml = agent.connection.filemanager.get(path)
        except (exc.HTTPException, httplib.HTTPException,
                EnvironmentError) as e:
            self.error("filemanager.get(%s) on %s failed with: %s",
                       path, agent.displayname, str(e))
            return

        body = self.agentmanager.update_agent_yml(agent.agentid, yml)
        return body

    def maint(self, action, port=-1, aconn=None, send_alert=True):
        if action not in ("start", "stop"):
            self.log.error("Invalid maint action: %s", action)
            return self.error("Bad maint action: %s" % action)

        manager = self.agentmanager

        # FIXME: Tie agent to domain
        if not aconn:
            aconn = manager.agent_conn_by_type(AgentManager.AGENT_TYPE_PRIMARY)
            if not aconn:
                return self.error("maint: no primary agent is connected.")

        send_body = {"action": action}
        if port > 0:
            send_body["port"] = port

        body = self.send_immediate(aconn, "POST", "/maint", send_body)

        if body.has_key("error"):
            if action == "start":
                self.event_control.gen(\
                    EventControl.MAINT_START_FAILED,
                            dict({'error': body['error']}.items() +  \
                                                 aconn.__dict__.items()))
            else:
                self.event_control.gen(\
                    EventControl.MAINT_STOP_FAILED,
                            dict({'error': body['error']}.items() +  \
                                                 aconn.__dict__.items()))
            return body

        if not send_alert:
            return body

        if action == 'start':
            self.event_control.gen(EventControl.MAINT_ONLINE, aconn.__dict__)
        else:
            self.event_control.gen(EventControl.MAINT_OFFLINE, aconn.__dict__)

        return body

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

        self.log.debug(\
            "about to send an immediate command to '%s', type '%s', " + \
                "method '%s', uri '%s', body '%s'",
                    aconn.displayname, aconn.agent_type, method, uri, send_body)

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
                            aconn.displayname, res.status, method, uri, rawbody)
                self.remove_agent(aconn,\
                    ("Communication failure with agent. " +\
                    "Immediate command to %s, status returned: " +\
                    "%d: %s %s, body: %s") % \
                        (aconn.displayname, res.status, method, uri, rawbody))
                return self.httperror(res, agent=aconn.displayname,
                                      method=method, uri=uri, body=rawbody)
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

        self.agentmanager.set_displayname(aconn, uuid, displayname)

    def ziplogs_cmd(self, aconn, target=None):
        """Run tabadmin ziplogs'."""

        ziplog_name = time.strftime("%Y%m%d_%H%M%S") + ".logs.zip"
        install_dir = aconn.auth['install-dir']
        ziplog_path = ntpath.join(install_dir, "Data", ziplog_name)

        cmd = 'tabadmin ziplogs -l -n -a \\\"%s\\\"' % ziplog_path
        body = self.cli_cmd(cmd, aconn)
        body[u'info'] = u'tabadmin ziplogs -l -n -a ziplog_name'
        return body

    def error(self, msg, return_dict={}):
        """Returns error dictionary in standard format.  If passed
           a return_dict, then adds to it, otherwise a new return_dict
           is created."""

        return_dict['error'] = unicode(msg)
        return return_dict

    def httperror(self, res, error='HTTP failure',
                  agent=None, method='GET', uri=None, body=None):
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
        if agent:
            d['agent'] = agent
        return d;

    def init_new_agent(self, agent):
        """Agent-related configuration on agent connect.
            Args:
                aconn: agent connection
            Returns:
                True:  The agent responded correctly.
                False: The agent responded incorrectly.
        """

        YML_CONFIG_FILE_PART=ntpath.join("data", "tabsvc",
                                         "config", "workgroup.yml")

        aconn = agent.connection

        body = self.info(agent)
        if body.has_key("error"):
            self.log.error("Couldn't run info command on %s: %s",
                            aconn.displayname, body['error'])
            return False

        self.log.debug("info returned from %s: %s", aconn.displayname, str(body))
        if agent.tableau_install_dir:
            # FIXME: don't duplicate the data
            agent.agent_type = aconn.agent_type \
                = AgentManager.AGENT_TYPE_PRIMARY

            if agent.tableau_install_dir.find(':') == -1:
                self.log.error("agent %s is missing ':': %s for %s",
                               aconn.displayname, TABLEAU_INSTALL_DIR,
                               agent.tableau_install_dir)
                return False
            self.yml(agent)
        else:
            if self.agentmanager.is_tableau_worker(agent.ip_address):
                aconn.agent_type = AgentManager.AGENT_TYPE_WORKER
            else:
                aconn.agent_type = AgentManager.AGENT_TYPE_ARCHIVE

        # Cleanup.
        if agent.agent_type == AgentManager.AGENT_TYPE_PRIMARY:
            # Put into a known state
            body = self.maint("stop", aconn=aconn, send_alert=False)
            if body.has_key("error"):
                self.event_control.gen(\
                   EventControl.MAINT_STOP_FAILED,
                            dict(d.items() + aconn.__dict__.items()))

        body = self.archive(aconn, "stop")
        if body.has_key("error"):
            self.event_control.gen(EventControl.ARCHIVE_STOP_FAILED,
                                   dict(body.items() + aconn.__dict__.items()))
        # Get ready.
        body = self.archive(aconn, "start")
        if body.has_key("error"):
            self.event_control.gen(EventControl.ARCHIVE_START_FAILED,
                            dict(body.items() + aconn.__dict__.items()))

        # If tableau is stopped, turn on the maintenance server
        if agent.agent_type != AgentManager.AGENT_TYPE_PRIMARY:
            return True

        main_state = self.stateman.get_state()
        if main_state == StateManager.STATE_STOPPED:
            body = self.maint("start", aconn=aconn, send_alert=False)
            if body.has_key("error"):
                self.event_control.gen(EventControl.MAINT_START_FAILED,
                            dict(body.items() + aconn.__dict__.items()))

        return True

    def remove_agent(self, aconn, reason="", gen_event=True):
        manager = self.agentmanager
        manager.remove_agent(aconn, reason=reason, gen_event=gen_event)
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
        flush(self)

    def flush(self):
        self.writeln(self.buf)
        self.buf = ''

def main():
    import argparse
    import logger

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
    max_overflow = config.getint("database", "max_overflow", default=10)

    # engine is once per single application process.
    # see http://docs.sqlalchemy.org/en/rel_0_9/core/connections.html
    meta.engine = sqlalchemy.create_engine(url, echo=echo,
                                           max_overflow=max_overflow)
    # Create the table definition ONCE, before all the other threads start.
    meta.Base.metadata.create_all(bind=meta.engine)
    meta.Session = scoped_session(sessionmaker(bind=meta.engine))

    log.debug("Starting agent listener.")

    server = Controller((host, port), CliHandler)
    server.config = config
    server.log = log
    server.cli_get_status_interval = \
      config.getint('controller', 'cli_get_status_interval', default=10)

    Domain.populate()
    domainname = config.get('palette', 'domainname')
    server.domain = Domain.get_by_name(domainname)
    Environment.populate()
    server.environment = Environment.get()

    server.event = EventManager(server.domain.domainid)

    server.alert_email = AlertEmail(server)
    EventControl.populate()
    server.event_control = EventControlManager(server)

    server.system = SystemManager(server.domain.domainid)
    SystemManager.populate()

    StateControl.populate()

    server.auth = AuthManager(server)
    Role.populate()
    UserProfile.populate()

    workbook_manager = WorkbookManager(server.domain.domainid)
    workbook_manager.populate()

    server.backup = BackupManager(server.domain.domainid)

    manager = AgentManager(server)
    server.agentmanager = manager

    manager.update_last_disconnect_time()
    manager.start()

    # Need to instantiate to initialize state and status tables,
    # even if we don't run the status thread.
    statusmon = TableauStatusMonitor(server, manager)
    server.statusmon = statusmon

    server.sched = Sched(server)
    server.sched.populate()

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
