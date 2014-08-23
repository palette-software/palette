import ntpath

from storage import StorageConfig

from agentinfo import AgentVolumesEntry
from agent import Agent
from agentmanager import AgentManager
from util import sizestr

class DiskException(Exception):
    def __init__(self, errmsg):
        Exception.__init__(self, errmsg)

# This a transitory class - instantiated each time it is needed.
class DiskCheck(object):
    """Checks the backup and sets the target/location information."""

    def __init__(self, server, agent, parent_dir):
        # inputs
        self.server = server
        self.log = server.log

        self.agent = agent
        self.parent_dir = parent_dir     # "backup", or "ziplogs"

        # outputs
        self.target_type = None  # StorageConfig.VOL, GCS or S3.

        self.target_entry = None
        self.target_agent = None
        self.target_vol = ""
        self.target_dir = ""
        self.min_target_disk_needed = .3 * agent.tableau_data_size

        # Stores the directory where should the backup, etc. be done.
        # It may be the final destination directory or it could be temporarily
        # used before copying to the cloud or other agent.
        self.primary_dir = ""
        self.primary_entry = None

        self.primary_dir_is_palette_primary_data_volume = False

        # Whether or not the primary agent is the final destination.
        self.primary_final_dest = True

        self.set_locs()

    def set_locs(self):
        """Set backup volume location based on free disk and volumes
           available.
        """
        if not self.agent.tableau_data_dir:
            raise DiskException(
                "Missing 'tableau_data_dir' in pinfo.  Cannot proceed.")

        try:
            self.storage_config = StorageConfig(self.server.system)
        except ValueError, e:
            raise DiskException(e)

        # Determine the target info.
        self.set_target_from_config()

    def set_target_from_config(self):
        """Use the user configuration settings from StorageConfig
           to set and check a target type and entry, etc.
         """

        self.target_agent = None
        self.target_entry = None
        self.target_type = None
        self.target_entry_is_palette_data_area = False
        self.primary_final_dest = False

        if self.storage_config.backup_dest_type == StorageConfig.GCS:
            entry = self.server.gcs.get_by_gcsid(
                                            self.storage_config.backup_dest_id)

            if not entry:
                raise DiskException(
                        "gcsid not found: %d" % storage_config.backup_dest_id)

            self.target_entry = entry
            self.target_type = StorageConfig.GCS
            self.primary_final_dest = False
            self.set_primary_dir()
            return
        elif self.storage_config.backup_dest_type == StorageConfig.S3:
            entry = self.server.s3.get_by_s3id(
                                            self.storage_config.backup_dest_id)

            if not entry:
                raise DiskException(
                    "s3id not found: %d" % self.storage_config.backup_dest_id)

            self.target_entry = entry
            self.target_type = StorageConfig.S3
            self.primary_final_dest = False
            self.set_primary_dir()
            return
        elif self.storage_config.backup_dest_type == StorageConfig.VOL:
            self.config_vol_target()
            return
        else:
            raise DiskException("diskcheck: Invalid backup dest_type: %s" % \
                                        self.storage_config.backup_dest_type)

    def config_vol_target(self):
        # Backup is configured to go to a volume.
        entry = AgentVolumesEntry.get_vol_entry_by_volid(
                                        self.storage_config.backup_dest_id)
        
        if not entry:
            raise DiskException(
                    "volid not found: %d" % self.storage_config.backup_dest_id)

        self.target_entry = entry
        self.target_type = StorageConfig.VOL

        target_agent = Agent.get_by_id(entry.agentid)
        if not target_agent:
            raise DiskException(
                "No such agentid %d referenced by volid %d in backupid %d" % \
                (entry.agentid, entry.volid,
                                        self.storage_config.backup_dest_id))

        # Check to see if this volume has enough available disk space.
        if entry.available_space < self.min_target_disk_needed:
            raise DiskException(
                ("Not enough available space on '%s' volume '%s' volid %d: " + \
                 "Available space: " +
                "%s, needed: %s") % \
                        (target_agent.displayname,
                        entry.name, entry.volid, sizestr(entry.available_space),
                        sizestr(self.min_target_disk_needed)))

        # Check if the backup would use more disk space than is allowed
        # by the "archive_limit" in the volume entry.
        if entry.size - entry.available_space + self.min_target_disk_needed > \
                                                    entry.archive_limit:
            raise DiskException(
                ("Minimum space needed greater than archive limit." + \
                "volid: %d.  Need: %s.  With backup vol would have: %s.  " + \
                "Allowed/archive limit: %s") % \
                (entry.volid, sizestr(self.min_target_disk_needed),
                sizestr(entry.size - entry.available_space + \
                            self.min_target_disk_needed), sizestr(entry.archive_limit)))

        self.target_agent = target_agent
        self.target_vol = entry.name
        # fixme: agent.path...
        self.target_dir = ntpath.join(entry.name + ":\\", entry.path,
                                                          self.parent_dir)

        if self.target_agent.agentid == self.agent.agentid:
            self.primary_dir = self.target_dir
            self.primary_entry = self.target_entry
            self.primary_final_dest = True
        else:
            self.primary_final_dest = False
            # Find a good directory to use on the primary before
            # copying to the agent.
            self.set_primary_dir()

        self.log.debug("check_volume_from_config: set target to " + \
                "agent '%s', volid %d, target dir '%s', " + \
                "primary_dir '%s'. " + \
                "Need %s, have %s, size %s, " + \
                "archive limit %s",
                    agent.displayname, entry.volid, self.target_dir,
                    self.primary_dir,
                    sizestr(self.min_target_disk_needed),
                                        sizestr(entry.available_space),
                    sizestr(entry.size), sizestr(entry.archive_limit))

    def set_primary_dir(self):
        """
            Find a directory on the primary that can temporarily hold
            the backup, etc. before it is copied to another agent or cloud.
        """

        for volume in \
            AgentVolumesEntry.get_vol_entries_by_agentid(self.agent.agentid):

            if volume.available_space > self.min_target_disk_needed:
                # fixme: agent.path... and support linux
                self.primary_dir = volume.name + ":" + volume.path + \
                                                "\\" + self.parent_dir
                self.primary_entry = volume
                return

        raise DiskException("There is not enough disk space on any " + \
            "volumes on the Tableau Primary to temporarily hold the " + \
            "backup before copying.")
