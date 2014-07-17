import ntpath

from storage import StorageConfig

from agentinfo import AgentVolumesEntry
from agent import Agent

class DiskException(Exception):
    def __init__(self, errmsg):
        Exception.__init__(self, errmsg)

# This a transitory class - instantiated each time it is needed.
class DiskCheck(object):
    """Checks the backup and sets the target/location information."""

    def __init__(self, server, agent):
        # inputs
        self.server = server
        self.log = server.log

        self.agent = agent

        # outputs
        self.target_type = None  # StorageConfig.VOL, GCS or S3.

        self.target_entry = None
        self.target_agent = None
        self.target_dir = ""
        self.min_target_disk_needed = .3 * agent.tableau_data_size

        self.set_locs()

    def set_locs(self):
        """Set backup volume location based on free disk and volumes
        available.
        """
        if not self.agent.tableau_data_dir:
            raise DiskException(
                "Missing 'tableau_data_dir' in pinfo.  Cannot proceed.")

        # Check primary agent for disk availability
        self.primary_check()

        # We now know the primary has enough space.
        # Determine the target info.
        self.set_target_from_config()

    def primary_check(self):
        """Check to see if the primary has enough available disk space.
        Returns:
            True: primary has enough disk space
            False: primary does NOT have enough disk space
        """

        min_primary_disk_needed = self.agent.tableau_data_size

        # e.g. "C:"
        tableau_data_dir = self.agent.tableau_data_dir
        primary_data_volume = self.agent.tableau_data_dir.split(':')[0]

        volumes = \
            AgentVolumesEntry.get_vol_entries_by_agentid(self.agent.agentid)

        volume_l = [vol for vol in volumes if vol.name == primary_data_volume]

        if not volume_l:
            raise DiskException(
                ("Missing volume/disk available information from pinfo for " + \
                "'%s' volume '%s'") % \
                    (self.agent.displayname, primary_data_volume))

        primary_volume = volume_l[0]

        primary_available = primary_volume.available_space

        if primary_available < min_primary_disk_needed:
            raise DiskException(
                ("Cannot backup due to shortage of disk space on " + \
                "primary host '%s': %d needed, but only %d available.") % \
                    (self.agent.displayname,
                     min_primary_disk_needed,
                     primary_available))

        self.log.debug(\
            "primary_check: primary has enough space.  Need %d and have %d",
            min_primary_disk_needed, primary_available)

    def set_target_from_config(self):
        """Use the user configuration settings from StorageConfig
           to set and check a target type and entry, etc.

           Returns:
                True - no error
                False - error
         """

        self.target_agent = None
        self.target_entry = None
        self.target_type = None

        try:
            storage_config = StorageConfig(self.server)
        except ValueError, e:
            raise DiskExceptio(e)

        if storage_config.backup_dest_type == StorageConfig.GCS:
            entry = self.server.gcs.get_by_gcsid(\
                                            storage_config.backup_dest_id)

            if not entry:
                raise DiskException(\
                        "gcsid not found: %d" % storage_config.backup_dest_id)

            self.target_entry = entry
            self.target_type = StorageConfig.GCS
            return entry
        elif storage_config.backup_dest_type == StorageConfig.S3:
            entry = self.server.s3.get_by_s3id(\
                                            storage_config.backup_dest_id)

            if not entry:
                raise DiskException(\
                        "s3id not found: %d" % storage_config.backup_dest_id)

            self.target_entry = entry
            self.target_type = StorageConfig.S3
            return entry
        elif storage_config.backup_dest_type != StorageConfig.VOL:
            # sanity check
            raise DiskException("diskcheck: Invalid backup dest_type: %s" % \
                                            storage_config.backup_dest_type)

        entry = AgentVolumesEntry.get_vol_entry_by_volid(\
                                                storage_config.backup_dest_id)
        
        if not entry:
            raise DiskException(\
                    "volid not found: %d" % storage_config.backup_dest_id)

        self.target_entry = entry
        self.target_type = StorageConfig.VOL

        # Check to see if this volume has enough available disk space.
        if entry.available_space < self.min_target_disk_needed:
            raise DiskException(\
                ("Not enough available space on volid %d: Available space: " +
                "%d, needed: %d") % (entry.volid, entry.available_space,
                                                self.min_target_disk_needed))

        # Check if the backup would use more disk space than is allowed
        # by the "archive_limit" in the volume entry.
        if entry.size - entry.available_space + self.min_target_disk_needed > \
                                                    entry.archive_limit:
            raise DiskException(\
                ("Minimum space needed greater than archive limit." + \
                "volid: %d.  Need: %d.  With backup vol would have: %d.  " + \
                "Allowed/archive limit: %d") % \
                (entry.volid, self.min_target_disk_needed,
                entry.size - entry.available_space + \
                            self.min_target_disk_needed, entry.archive_limit))
        agent = Agent.get_by_id(entry.agentid)
        if not agent:
            raise DiskException(\
                "No such agentid %d referenced by volid %d in backupid %d" % \
                                entry.agentid, entry.volid, entry.backupid)

        self.target_agent = agent
        self.target_dir = ntpath.join(entry.name + ":\\", entry.path)

        self.log.debug("check_volume_from_config: set target to " + \
                "agent '%s', volid %d, target dir '%s'. " + \
                "Need %d, have %d, size %d, " + \
                "archive limit %d",
                    agent.displayname, entry.volid, self.target_dir,
                    self.min_target_disk_needed, entry.available_space,
                                            entry.size, entry.archive_limit)
