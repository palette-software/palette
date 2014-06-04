import ntpath

from sqlalchemy.orm.exc import NoResultFound

from akiri.framework.ext.sqlalchemy import meta

from agentinfo import AgentInfoEntry, AgentVolumesEntry
from agentstatus import AgentStatusEntry
from agentmanager import AgentManager

class DiskCheck(object):
    """Checks the target and volume for backups."""

    def __init__(self, server, aconn, target=None, volume_name=None):
        # inputs
        self.server = server
        self.agentmanager = server.agentmanager
        self.log = server.log

        self.aconn = aconn
        self.target = target
        self.volume_name = volume_name
        self.error_msg = None

        # outputs
        self.target_conn = None
        self.target_dir = ""
        self.vol_entry = None
        self.min_target_disk_needed = .3 * \
                        aconn.pinfo[AgentInfoEntry.TABLEAU_DATA_SIZE_KEY]

    def error(self, msg):
        self.error_msg = msg
        return False

    def set_locs(self):
        """Set backup volume location based on free disk and volumes
        available.
            Returns:
                    True on success
                    Fail on error.  Also sets self.error to the
                    error message.
        """
        if not AgentInfoEntry.TABLEAU_DATA_DIR_KEY in self.aconn.pinfo:
            return self.error(\
                    "Missing '%s' in pinfo.  Cannot proceed with backup." % \
                                    AgentInfoEntry.TABLEAU_DATA_DIR_KEY)

        # Check primary agent for disk availability
        if not self.primary_check():
            return self.error_msg

        # We now know the primary has enough space.
        # Determine the target volume.
        if not self.target_check():
            return False

        return True

    def primary_check(self):
        """Check to see if the primary has enough available disk space.
        Returns:
            True: primary has enough disk space
            False: primary does NOT have enough disk space
        """

        min_primary_disk_needed = \
            self.aconn.pinfo[AgentInfoEntry.TABLEAU_DATA_SIZE_KEY] * 2

        # e.g. "C:"
        primary_data_volume = \
            self.aconn.pinfo[AgentInfoEntry.TABLEAU_DATA_DIR_KEY].split(':')[0]

        volume_l = [vol for vol in self.aconn.pinfo['volumes'] \
                                        if vol['name'] == primary_data_volume]

        if not volume_l:
            return self.error(\
                ("Missing volume/disk available information from pinfo for " + \
                "'%s' volume '%s'") % \
                                (self.aconn.displayname, primary_data_volume))

        primary_volume = volume_l[0]

        if not "available-space" in primary_volume:
            return self.error(("Missing 'available-space' value from " + \
                            "pinfo for '%s' primary volume '%s'") % \
                                (self.aconn.displayname, primary_data_volume))

        primary_available = primary_volume['available-space']

        if primary_available < min_primary_disk_needed:
            return self.error(\
                ("Cannot backup due to shortage of disk space on " + \
                "primary host '%s': %d needed, but only %d available." ) % \
                    (self.aconn.displayname, min_primary_disk_needed,
                                                        primary_available))

        self.log.debug(\
            "primary_check: primary has enough space.  Need %d and have %d",
                                    min_primary_disk_needed, primary_available)

        return True

    def target_check(self):
        """Determines the target and volume."""

        if self.target:
            return self.set_target()
        else:
            return self.we_choose_target_and_vol()

    def set_target(self):
        """We were passed a target.  Look for the target
        in active agent connections and set the volume."""

        # target_conn is the destination agent - if applicable.
        self.target_conn = None

        agents = self.agentmanager.all_agents()
        for key in agents:
            if agents[key].displayname == self.target:
                # FIXME: make sure agent is connected
                if agents[key].agent_type != \
                                      AgentManager.AGENT_TYPE_PRIMARY:
                    self.target_conn = agents[key]
                break

        if not self.target_conn:
            return self.error(\
                "agent '%s' does not exist or is offline or is a " + \
                                        "primary agent" % self.target)

        # The target agent has been found.
    
        # Set the volume.
        if self.volume_name:
            return self.set_volume()
        else:
            return self.we_choose_volume()

    def we_choose_target_and_vol(self):
        # We weren't passed a specific target to copy the backup to.
        # Get the current order of agents, according to the database
        # column "display_order".
        agent_keys_sorted = \
            AgentStatusEntry.display_order_by_domainid(self.server.domainid)

        agents = self.agentmanager.all_agents()
        for key in agent_keys_sorted:
            if not agents.has_key(key):
                self.error("we_choose_target: agent in memory not in " + \
                                                    "db! agentid: %s" % key)
                continue

            self.log.debug("we_choose_target: Checking agent %s", \
                                                agents[key].displayname)
            if agents[key].agent_type != AgentManager.AGENT_TYPE_PRIMARY:
                # FIXME: make sure agent is connected
                # FIXME: ticket #218: When the UI supports selecting
                #        a target, remove the code that automatically
                #        selects a remote.

                # Check to see if this target has a volume
                # with enough available disk space.
                vol_entry = AgentVolumesEntry.has_available_space(\
                            agents[key].agentid, self.min_target_disk_needed)

                if not vol_entry:
                    self.log.debug("we_choose_target: No space on '%s'",
                                            agents[key].displayname)
                    continue # Not enough available space on this target

                self.vol_entry = vol_entry
                self.target_conn = agents[key]
                self.target_dir = ntpath.join(vol_entry.name + ":/",
                                                            vol_entry.path)

                self.log.debug("we_choose_target: set target to " + \
                    "agent '%s', volid %d, target dir '%s'. " + \
                    "Need %d, have %d, size %d, " + \
                    "archive limit %d",
                        agents[key].displayname,
                        vol_entry.volid,
                        self.target_dir,
                        self.min_target_disk_needed,
                                vol_entry.available_space, vol_entry.size, 
                                                    vol_entry.archive_limit)

                return True

        # No suitable target was found so leave the backup on the primary.
        return False

    def set_volume(self):
        """We were also passed the volume name to use.  Check to
        see if it can be used.
            Returns:
                True - can be used
                False - can't be used.
        """

        self.volume_name = self.volume_name.upper()
        try:
            entry = meta.Session.query(AgentVolumesEntry).\
                filter(AgentVolumesEntry.agentid == \
                                            self.target_conn.agentid).\
                filter(AgentVolumesEntry.name == self.volume_name).\
                one()
        except NoResultFound, e:
                return self.error(("backup: Volume '%s' not found " + \
                    "on target '%s'") % (self.volume_name, self.target))
    
        if not entry.archive:
            return self.error(("backup: Volume '%s' on target '%s' " + \
                "is not an 'archive'") % (self.volume_name, self.target))

        if entry.available_space < self.min_target_disk_needed:
            return self.error(("backup: Volume '%s' on target  " +  \
                "'%s' does not have the minumum available " + \
                "space: %d. Has only %d.") % (self.volume_name, self.target,
                entry.available_space, self.min_target_disk_needed,
                                            entry.available_space))

        if entry.size - entry.available_space + \
                                    self.min_target_disk_needed > \
                                                entry.archive_limit:
            return self.error(("backup: Volume '%s' on target " + \
                    "'%s' has a smaller archive-limit (%d) than " + \
                    "would be needed with this backup " + \
                    "(%d - %d + %d = %d)") % (self.volume_name, self.target,
                        entry.archive_limit,
                        entry.size - entry.available_space +  \
                                            self.min_target_disk_needed))
        self.target_dir = ntpath.join(entry.name + ":", entry.path)
        self.vol_entry = entry

        return True

    def we_choose_volume(self):
        """Volume wasn't specified.
        Check to see if this target has a volume
        with enough available disk space.
            Returns:
                True: we found a volume.
                False: no suitable volume was found.
        """

        vol_entry = AgentVolumesEntry.has_available_space(\
                        self.target_conn.agentid, self.min_target_disk_needed)

        if not vol_entry:
            return self.error("we_choose_volume: No space on chosen " + \
                            "target '%s'" % agents[key].displayname)

        self.target_dir = ntpath.join(vol_entry.name + ":", 
                                                        vol_entry.path)
        self.vol_entry = vol_entry

        return True
