from general import SystemConfig
from files import FileManager

from agent import AgentVolumesEntry
from agent import Agent
from util import sizestr

class DiskException(Exception):
    def __init__(self, errmsg):
        Exception.__init__(self, errmsg)

# This a transitory class - instantiated each time it is needed.
class DiskCheck(object):
    # pylint: disable=too-many-instance-attributes
    """Sets the location for:
        - the initial command (if staging is needed)
        - The target/location (if a different final location is needed,
          like a different agent+volume).
        - Make directories on the primary that are referenced here.
    """

    def __init__(self, server, agent, parent_dir, file_type,
                 min_disk_needed):
        # pylint: disable=too-many-arguments

        # inputs
        self.server = server
        self.log = server.log

        self.agent = agent
        self.parent_dir = parent_dir     # "backup", or "ziplogs"
        self.file_type = file_type

        # outputs
        self.target_type = None  # FileManager.STORAGE_TYPE_VOL or CLOUD

        self.target_entry = None
        self.target_agent = None
        self.target_dir = ""    # Not used for cloud storage
        self.min_disk_needed = min_disk_needed

        # Specifies the directory where should the file should be
        # created, initially.
        # It may be the final destination directory or it could be temporarily
        # used before copying to the cloud or other agent.
        self.primary_dir = ""
        self.primary_entry = None

        # Whether or not the primary agent is the final destination.
        self.primary_final_dest = True

        try:
            self.storage_config = SystemConfig(self.server.system)
        except ValueError, ex:
            raise DiskException(ex)

        # Determine the target info.
        self._set_target_from_config()

        self._mkdirs()

    def _set_locs(self):
        """Set file agent/volume location based on free disk and volumes
           available.
        """

    def _set_target_from_config(self):
        """Use the user configuration settings from SystemConfig
           to set and check a target type and entry, etc.
         """

        self.primary_final_dest = False

        if self.storage_config.backup_dest_type == FileManager.STORAGE_TYPE_VOL:
            self._config_vol_target()
            return
        elif self.storage_config.backup_dest_type == \
                                                FileManager.STORAGE_TYPE_CLOUD:
            self._config_cloud_target()
        else:
            raise DiskException("diskcheck: Invalid backup dest_type: %s" % \
                                self.storage_config.backup_dest_type)

    def _mkdirs(self):
        """Make sure the primary agent directories exists."""

        try:
            self.agent.filemanager.mkdirs(self.primary_dir)
        except (IOError, ValueError) as ex:
            self.log.error(
                "diskcheck.mkdirs: Could not create directory: '%s': %s",
                self.primary_dir, str(ex))
            raise DiskException("Could not create directory '%s': %s" % \
                                (self.primary_dir, str(ex)))

        # Create directories only on the primary
        if self.target_agent != self.agent:
            return

        if self.target_dir and (self.primary_dir != self.target_dir):
            # Make sure the target directory on the primary exists, too.
            try:
                self.agent.filemanager.mkdirs(self.target_dir)
            except (IOError, ValueError) as ex:
                self.log.error("diskcheck.mkdirs: Could not create " + \
                               "target directory: '%s': %s",
                                self.target_dir, str(ex))
                raise DiskException(
                    ("Could not create target directory " + \
                                 "'%s': %s") % (self.target_dir, str(ex)))


    def _config_cloud_target(self):
        """File is configured to go to the cloud."""
        entry = self.server.cloud.get_by_cloudid(
                                            self.storage_config.backup_dest_id)

        if not entry:
            raise DiskException("cloudid not found: %d" % \
                                 self.storage_config.backup_dest_id)

        self.target_entry = entry
        self.target_type = FileManager.STORAGE_TYPE_CLOUD
        self.primary_final_dest = False
        # Get the location to backup/ziplogs or stage to
        (self.primary_dir, self.primary_entry) = \
               DiskCheck.get_primary_loc(self.agent,
                                         self.parent_dir,
                                         self.min_disk_needed)
        self.log.debug("cloud: primary_dir: %s", self.primary_dir)
        return

    def _config_vol_target(self):
        # File is configured to go to an agent.
        entry = AgentVolumesEntry.get_vol_entry_by_volid(
                                    self.storage_config.backup_dest_id)

        if not entry:
            raise DiskException(
                    "volid not found: %d" % self.storage_config.backup_dest_id)

        self.target_entry = entry
        self.target_type = FileManager.STORAGE_TYPE_VOL

        target_agent = Agent.get_by_id(entry.agentid)
        if not target_agent:
            raise DiskException(
                "No such agentid %d referenced by volid %d in backupid %d" % \
                (entry.agentid, entry.volid,
                                        self.storage_config.backup_dest_id))

        if not target_agent.enabled:
            raise DiskException(("Cannot save to Storage Location on " + \
                                "agent '%s': agent is disabled.") % \
                                target_agent.displayname)

        # Check to see if this volume has enough available disk space.
        if entry.available_space < self.min_disk_needed:
            raise DiskException(
                ("Not enough available space on '%s' volume '%s' volid %d: " + \
                 "Available space: " +
                "%s, needed: %s") % \
                        (target_agent.displayname,
                        entry.name, entry.volid, sizestr(entry.available_space),
                        sizestr(self.min_disk_needed)))

        # Check if the backup/ziplog would use more disk space than is allowed
        # by the "archive_limit" in the volume entry.
        if entry.size - entry.available_space + self.min_disk_needed > \
                                                    entry.archive_limit:
            raise DiskException(
                ("Minimum space needed greater than archive limit." + \
                "volid: %d.  Need: %s.  With vol would have: %s.  " + \
                "Allowed/archive limit: %s") % \
                (entry.volid, sizestr(self.min_disk_needed),
                sizestr(entry.size - entry.available_space + \
                            self.min_disk_needed),
                            sizestr(entry.archive_limit)))

        self.target_agent = target_agent
        # fixme: agent.path...
        self.target_dir = entry.name + ":" +  entry.path + \
                                               "\\" + self.parent_dir

        if self.target_agent.agentid == self.agent.agentid:
            self.primary_dir = self.target_dir
            self.primary_entry = self.target_entry
            self.primary_final_dest = True
        else:
            self.primary_final_dest = False
            # Get the location to backup/ziplog or stage to
            (self.primary_dir, self.primary_entry) = \
                   DiskCheck.get_primary_loc(self.agent,
                                self.parent_dir,
                                self.min_disk_needed)

        self.log.debug("check_volume_from_config: set target to " + \
                "agent '%s', volid %d, target dir '%s', " + \
                "primary_dir '%s'. " + \
                "Need %s, have %s, size %s, " + \
                "archive limit %s",
                   self.target_agent.displayname, entry.volid, self.target_dir,
                   self.primary_dir,
                   sizestr(self.min_disk_needed),
                                        sizestr(entry.available_space),
                   sizestr(entry.size), sizestr(entry.archive_limit))

    @classmethod
    def get_primary_loc(cls, agent, parent_dir, min_disk_needed=0):
        """
            Find a directory on the primary that can temporarily hold
            the backup/ziplog, etc. before it is copied to another
            agent or cloud, or used for restore, etc.

            Arguments:
                agent
                minimum_disk_needed     bytes needed on the volume, unless 0
                parent_dir:             The directory name to add, such as:
                                        'backup', 'ziplogs', etc.

        """

        for volume in \
            AgentVolumesEntry.get_vol_archive_entries_by_agentid(agent.agentid):

            if not min_disk_needed or volume.available_space > min_disk_needed:
                # fixme: agent.path... and support linux
                primary_dir = volume.name + ":" + volume.path + \
                                                "\\" + parent_dir
                primary_entry = volume

                return (primary_dir, primary_entry)

        raise DiskException("There is not enough disk space on any " + \
            "volumes on the Tableau Primary to temporarily hold the " + \
            "file for this operation.")
