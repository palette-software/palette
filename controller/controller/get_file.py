import os

from agent import Agent
from agentinfo import AgentVolumesEntry
from cloud import CloudManager
from diskcheck import DiskCheck, DiskException
from files import FileManager

# This a transitory class - instantiated each time it is needed.
class GetFile(object):
    # pylint: disable=too-many-instance-attributes
    """Copies the full_path file, if needed, to the primary agent from
       another agent or cloud storage for use by commands
       such as 'tabadmin restore', etc."""

    def __init__(self, server, agent, full_path):
        self.server = server
        self.log = server.log
        self.files = server.files

        self.agent = agent
        self.full_path = full_path  # incoming

        self.file_entry = None

        self.source_type = None
        self.source_entry = None
        self.source_agent = None

        self.primary_dir = None
        self.primary_entry = None
        # The full pathname on the primary that can be used
        # the the restore/etc. command.  This will change
        # from "full_path" if copying from cloud storage or another agent.
        self.primary_full_path = self.full_path

        # Keep track of whether or not a file was copied to the primary
        # for the restore, etc..  If so, we'll need to delete the
        # file after the restore, etc. finishes or an error.
        self.copied = False

        self._get_file()

    def _get_file(self):
        self.file_entry = self.files.find_by_name(self.full_path)
        if not self.file_entry:
            raise IOError("File not found: %s" % self.full_path)

        # Sets self.source_type/entry.  Also sets self.agent if the
        # file is on an agent.
        self._set_source()

        # The case where the file is not on the primary.
        # Find a place to stage the file.
        self._set_primary()

        self._mkdir()

        if self.source_type == FileManager.STORAGE_TYPE_CLOUD:
            self._get_cloud_file()

        elif self.source_type == FileManager.STORAGE_TYPE_VOL and \
                        self.source_agent.agentid != self.agent.agentid:
            self._get_agent_file()

    def _mkdir(self):
        """Make sure the primary agent directory exists."""
        try:
            self.agent.filemanager.mkdirs(self.primary_dir)
        except (IOError, ValueError) as ex:
            self.log.error(
                "get_file.mkdirs: Could not create directory: '%s': %s",
                self.primary_dir, str(ex))
            raise IOError("Could not create directory '%s': %s" % \
                                (self.primary_dir, str(ex)))

    def _set_primary(self):
        """The case where the file is not on the primary.
           Find a place to stage the file."""
        if self.source_type == FileManager.STORAGE_TYPE_CLOUD or \
            ((self.source_type == FileManager.STORAGE_TYPE_VOL) and \
                    (self.source_agent.agentid != self.agent.agentid)):
            try:
                (self.primary_dir, self.primary_entry) = \
                    DiskCheck.get_primary_loc(self.agent,
                                              self.server.STAGING_DIR,
                                              self.file_entry.size)
            except DiskException, ex:
                self.log.error("get_file: get_primary_loc failed: %s",
                               str(ex))
                raise IOError("get_file: %s" % str(ex))
        else:
            self.primary_dir = self.agent.path.dirname(self.full_path)

        self.log.debug("get_file: primary_dir: %s", self.primary_dir)

    def _set_source(self):
        """Set:
            self.source_type: FileManager.STORAGE_CLOUD or
                              FileManager.STORAGE_TYPE_VOL
            self.source_entry:  The source file entry in cloud or agent_info
        """
        # Get the cloud or vol entry
        if self.file_entry.storage_type == FileManager.STORAGE_TYPE_CLOUD:
            self.source_type = FileManager.STORAGE_TYPE_CLOUD
            self.source_entry = \
                self.server.cloud.get_by_cloudid(self.file_entry.storageid)
            if not self.source_entry:
                raise IOError(
                            "get_file: cloud entry not found for cloudid %d" % \
                            self.file_entry.storageid)
        elif self.file_entry.storage_type == FileManager.STORAGE_TYPE_VOL:
            self.source_type = FileManager.STORAGE_TYPE_VOL
            self.source_entry = \
                AgentVolumesEntry.get_vol_entry_by_volid(
                                                    self.file_entry.storageid)

            if not self.source_entry:
                raise IOError("get_file: vol entry not found for volid %d" % \
                               self.file_entry.storageid)

            self.source_agent = Agent.get_by_id(self.source_entry.agentid)
            if not self.source_agent:
                raise IOError((
                    "_get_file: No such agentid %d referenced by " + \
                    "files entry %d and name %s") % \
                        (self.source_entry.agentid, self.file_entry.storageid,
                                            self.file_entry.name))
        else:
            raise IOError(("_get_file: Unknown file storage type " + \
                              "'%s' for file '%s'") % \
                              (self.file_entry.storage_type, self.full_path))

    def _get_cloud_file(self):
        """The file is on cloud storage: s3 or gcs.
            Copy it to a staging area.
        """
        self.log.debug(
            "get_file: Sending %s command to primary '%s' to GET '%s'", \
               self.source_type, self.agent.displayname, self.full_path)

        # Cloud storage doesn't support directories.  The
        # full_path on the cloud storage was only the filename.
        # We set primary_full_path to be the full path of where
        # we want to copy the file to on the primary.
        self.primary_full_path = self.agent.path.join(
                self.primary_dir,
                self.agent.path.basename(self.full_path))

        if self.source_entry.cloud_type == CloudManager.CLOUD_TYPE_GCS:
            cloud_cmd = self.server.gcs_cmd
        elif self.source_entry.cloud_type == CloudManager.CLOUD_TYPE_S3:
            cloud_cmd = self.server.s3_cmd

        # Where to store the cloud file
        data_dir = self.agent.path.dirname(self.primary_full_path)
        # NOte full_path for a cloud file will not have a directory.
        body = cloud_cmd(self.agent, "GET", self.source_entry,
                         data_dir, self.full_path)
        if 'error' in body:
            fmt = "_get_cloud_file: %s named '%s' GET file '%s' " + \
                "failed.  Error: %s"
            text = fmt % (self.source_type,
                       self.source_entry.name,
                       self.full_path,
                       body['error'])

            self.log.debug(text)
            raise IOError(text)

        self.copied = True

    def _get_agent_file(self):
        # The file isn't on the Primary agent or cloud storage.
        # We need to copy the file to the Primary.
        # copy_cmd arguments:
        #   source_agentid  <source-agentid>
        #   source_path:    VOL/tableau-backups/filename
        #   target_agentid: <target-agentid>
        #   target_dir:     palette-primary-data-path/tableau-backups
        # source_path is something like:
        #               "C/tableau-backups/20140531_153629.tsbak"
        # with only the "tableau-backup/20140531_153629.tsbak"
        # last part.

        # Remove the agent's volume and 'data-dir' portion from the beginning
        # of seilf.full_path.
        # For example, given:
        #   C:\ProgramData\Palette\Data\tableau-backups\2014.gone.tsbak
        # and a self.source_entry path of:
        #   C:\ProgramData\Palette\Data
        # end up with:
        #   \tableau-backups\2014.gone.tsbak

        (_, path_spec) = self.full_path.split(':', 1)

        common = os.path.commonprefix([path_spec,
                                      self.source_entry.path])
        if common:
            # Chop off the leading common part in routes.txt
            path_spec = path_spec[len(common):]

        copy_source = "%s%s" % (self.source_entry.name, path_spec)

        self.log.debug("get_file: Sending copy command to " + \
                       "agentid %d (%s) to get: %s",
                       self.source_agent.agentid, self.source_agent.displayname,
                       copy_source)

        body = self.server.copy_cmd(self.source_entry.agentid, copy_source,
                            self.agent.agentid, self.primary_dir)

        if body.has_key("error"):
            fmt = "get_file: copy file specification '%s' " + \
                  "from agent '%s' (agentid %d) to target agent '%s' " + \
                  "(agentid %d) directory '%s' failed.  Error was: %s"
            text = fmt % (copy_source,
                           self.source_agent.displayname,
                           self.source_agent.agentid,
                           self.agent.displayname,
                           self.agent.agentid,
                           self.primary_dir,
                           body['error'])
            self.log.debug(text)
            raise IOError(text)

        # This is the filename to use for 'tabadmin restore'
        # now that it is copied to the primary.
        self.primary_full_path = self.agent.path.join(self.primary_dir,
                            self.agent.path.basename(self.full_path))

        self.copied = True
