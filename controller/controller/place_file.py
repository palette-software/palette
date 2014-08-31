import os
import time

from cloud import CloudManager
from files import FileManager
from agentinfo import AgentVolumesEntry

# This a transitory class - instantiated each time it is needed.
class PlaceFile(object):
    """Copies the full_path, if needed to the primary agent from
       another agent or cloud storage for use by commands
       such as 'tabadmin restore', etc.."""

    def __init__(self, server, agent, dcheck, full_path, size, auto):

        self.server = server
        self.log = server.log

        self.copy_elapsed_time = 0

        self.agent = agent
        self.dcheck = dcheck
        self.full_path = full_path
        self.name_only = self.agent.path.basename(full_path)
        self.size = size
        self.auto = auto

        self.copy_failed = False
        self.delete_locale_backup = False
        self.copied = False
        self.info = ""

        self.do_copy()

    def do_copy(self):

        self.copy_start_time = time.time()

        if self.dcheck.target_type == FileManager.STORAGE_TYPE_CLOUD:
            self.copy_to_cloud()
        elif self.dcheck.target_agent.agentid != self.agent.agentid:
            self.copy_to_agent()
        elif self.dcheck.target_agent.agentid == self.agent.agentid:
            self.info = \
                    ('Backup file is configured to stay on ' + \
                    'the Tableau primary agent, ' + \
                    'data directory: %s') % self.dcheck.target_dir

            self.log.debug(self.info)
            self.delete_local_backup = False
            self.copy_failed = False
            self.copied = True
            self.server.files.add(self.full_path,
                            self.dcheck.file_type,
                            FileManager.STORAGE_TYPE_VOL,
                            self.dcheck.target_entry.volid,
                            size=self.size,
                            auto=self.auto)
            return

        if self.delete_local_backup:
            remove_body = self.server.delete_vol_file(self.agent,
                                                        self.full_path)
            # Check if the DEL worked.
            if remove_body.has_key('error'):
                self.info += \
                    ("\nDeletion of backup file failed after copy. "+\
                        "File: '%s'. Error was: %s") \
                        % (self.full_path, remove_body['error'])
                self.log.debug(self.info)

    def copy_to_cloud(self):
        if self.dcheck.target_entry.cloud_type == CloudManager.CLOUD_TYPE_S3:
            cloud_cmd = self.server.s3_cmd
        elif self.dcheck.target_entry.cloud_type == CloudManager.CLOUD_TYPE_GCS:
            cloud_cmd = self.server.gcs_cmd

        data_dir = self.agent.path.dirname(self.full_path)
        storage_body = cloud_cmd(self.agent, "PUT", self.dcheck.target_entry,
                                 data_dir, self.full_path)

        if 'error' in storage_body:
            self.info = ("Copy to %s bucket '%s' filename '%s' failed: %s." + \
                    "\nBackup will remain on the primary agent.") % \
                    (self.dcheck.target_entry.cloud_type,
                    self.dcheck.target_entry.bucket,
                    self.full_path,
                    storage_body['error'])
            self.log.debug(self.info)
            self.delete_local_backup = False
            self.copied = False
            self.copy_failed = True
            self.server.files.add(self.full_path,
                            self.dcheck.file_type,
                            FileManager.STORAGE_TYPE_VOL,
                            self.dcheck.primary_entry.volid,
                            size=self.size,
                            auto=self.auto)
        else:
            self.copy_elapsed_time = time.time() - self.copy_start_time
            self.info = \
                ("Backup file was copied to %s cloud bucket '%s' " + \
                 "filename '%s'.") % \
                (self.dcheck.target_entry.cloud_type,
                 self.dcheck.target_entry.bucket,
                 self.name_only)
            self.log.debug(self.info)
            # Backup was copied to gcs or s3
            self.server.files.add(self.name_only,
                            self.dcheck.file_type,
                            FileManager.STORAGE_TYPE_CLOUD,
                            self.dcheck.target_entry.cloudid,
                            size=self.size,
                            auto=self.auto)
            self.delete_local_backup = True
            self.copy_failed = False
            self.copied = True

    def copy_to_agent(self):
        # Copy the file to a non-primary agent
        # Example: "Tableau Archive #202:D/palette-backups/20140127_162225.tsbak"

        (backup_vol, backup_path) = self.full_path.split(':', 1)

        # Get the path used by routes.txt to find the common prefix
        source_agent_vol_entry = \
            AgentVolumesEntry.get_vol_entry_by_agentid_vol_name(
                                                self.agent.agentid, backup_vol)
        if not source_agent_vol_entry:
            return self.error(
                (u"Could not find backup volume '%s' for agentid %d. " + \
                "Backup will remain on the primary agent.") % \
                (backup_vol, self.agent.agentid))

        self.log.debug("backup_path: '%s' " + \
                       "source_agent_vol_entry.path: '%s'",
                       backup_path,
                      source_agent_vol_entry.path)
        common = os.path.commonprefix([backup_path,
                                      source_agent_vol_entry.path])

        if common:
            # Chop off the common part
            backup_path = backup_path[len(common):]

        source_path = "%s%s" % (backup_vol, backup_path)
        copy_start_time = time.time()
        copy_body = self.server.copy_cmd(self.agent.agentid, source_path,
                    self.dcheck.target_agent.agentid, self.dcheck.target_dir)

        if copy_body.has_key('error'):
            msg = (u"Copy of backup file '%s' to agent '%s:%s' failed. "+\
                "Will leave the backup file on the primary agent. " + \
                "Error was: %s") \
                % (self.full_path, self.dcheck.target_agent.displayname, 
                                self.dcheck.target_dir, copy_body['error'])
            self.log.info(msg)
            self.info += msg
            # Something was wrong with the copy to the non-primary agent.
            # Leave the backup on the primary after all.
            self.server.files.add(self.full_path,
                        self.dcheck.file_type,
                        FileManager.STORAGE_TYPE_VOL,
                        self.dcheck.primary_entry.volid,
                        size=self.size,
                        auto=self.auto)
            self.delete_local_backup = False
            self.copied = False
            self.copy_failed = True
        else:
            # The copy succeeded.
            self.copy_elapsed_time = time.time() - self.copy_start_time
            self.info += \
                "Backup file copied to agent '%s', directory: %s." % \
                (self.dcheck.target_agent.displayname, self.dcheck.target_dir)

            self.log.debug(self.info)
            target_full_path = self.dcheck.target_agent.path.join(
                                        self.dcheck.target_dir, self.name_only)

            self.server.files.add(target_full_path,
                            self.dcheck.file_type,
                            FileManager.STORAGE_TYPE_VOL,
                            self.dcheck.target_entry.volid,
                            size=self.size,
                            auto=self.auto)
            # Remember to remove the backup file from the primary
            self.delete_local_backup = True
            self.copy_failed = False
            self.copied = True
