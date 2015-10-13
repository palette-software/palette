import unicodedata

from place_file import PlaceFile
from sites import Site
from profile import UserProfile
from util import success

class ArchiveUpdateMixin(object):
    NAME = "unknown"

    def clean_filename(self, entry, revision):
        """Given an archive entry (datasource, workbook), create
           a unique, acceptable filename using the site, project, url, etc.
           Ideally: site-project-name-rev.ext"""

        site = entry.site
        if not site:
            site = str(entry.site_id)
        project = entry.project
        if not project:
            project = str(entry.project_id)
        filename = site + '-' + project + '-'
        filename += entry.repository_url + '-rev' + revision
        filename = filename.replace(' ', '_')
        filename = filename.replace('/', '_')
        filename = filename.replace('\\', '_')
        filename = filename.replace(':', '_')
        filename = unicodedata.normalize('NFKD', filename).encode('ascii',
                                                                  'ignore')
        return filename

    # See if credentials exist.
    def cred_check(self):
        """Returns None if there are credentials and Non-None/False
           if there are credentials."""

        cred = self.server.cred.get('primary', default=None)
        if not cred:
            cred = self.server.cred.get('secondary', default=None)

        if cred:
            if not cred.user:
                cred = None

        return cred

    def archive_file(self, agent, dcheck, dst):
        """Copy the given datasource filename from the Tableau server to
           its configured storage location.

           Returns:
                The PlaceFile instance.
        """

        # Get ready to move twbx /twb to resting location(s).
        file_size = 0
        try:
            file_size_body = agent.filemanager.filesize(dst)
        except IOError as ex:
            self.log.error("%s archive_file: filemanager.filesize('%s')" +
                           "failed: %s", self.NAME, dst, str(ex))
        else:
            if not success(file_size_body):
                self.log.error("%s archive_file: Failed to get size of " + \
                               "datasource file %s: %s", dst,
                               self.NAME, file_size_body['error'])
            else:
                file_size = file_size_body['size']

        # Save the datasource file on cloud storage, other agent,
        # or leave on the primary.
        auto = True
        # Note: If the file is copied off the primary, then it is deleted
        # from the primary afterwards, due to "enable_delete=True":
        place = PlaceFile(self.server, agent, dcheck, dst, file_size, auto,
                          enable_delete=True)
        self.log.debug("%s build filename %s: %s", self.NAME, dst, place.info)

        return place

    def sendevent(self, key, update, error, data):
        """Send the event."""

        if 'embedded' in data:
            del data['embedded']
        if error:
            self.log.error(error)
            data['error'] = error

        profile = UserProfile.get_by_system_user_id(
                                                self.server.environment.envid,
                                                update.system_user_id)

        if profile:
            username = profile.display_name()
            userid = profile.userid
        else:
            username = None
            userid = None

        if username and not 'owner' in data:
            data['owner'] = username

        return self.server.event_control.gen(key, data, userid=userid)

    def tabcmd_run(self, agent, url, dst, site_id):
        """Does the tabcmd_run to get the datasource or workbook file.
           Returns:
                True:   Returns dst (unchanged)
                False:  Fail
        """

        site_entry = Site.get(self.envid, site_id, default=None)

        if not site_entry:
            self.log.error("%s: Missing site id: %d", self.NAME, site_id)
            return {'error': 'Missing site id: %d' % site_id}

        if site_entry.url_namespace:
            site = '--site %s' % site_entry.url_namespace
        else:
            site = ''

        cmd = 'get %s %s -f "%s"' % (url, site, dst)

        self.log.debug('building %s archive: %s', self.NAME, dst)

        for _ in range(3):
            body = self.server.tabcmd(cmd, agent)
            if success(body):
                return body

            if 'stderr' not in body:
                continue    # try again

            # It failed and we have stderr.
            if 'Service Unavailable' in body['stderr']:
                # 503 error, retry
                self.log.debug(cmd + \
                                ' : 503 Service Unavailable, retrying')
                continue
            else:
                # It failed for another reason. Don't try again now.
                return body

        return body

    def get_archive_file_type(self, agent, dst):
        """Inspects the 'dst' file, checks to make sure it's valid.
            Returns:
                file_type ("xml" or "zip") on success
                raises an IOError exception on failure to recognize file type
       """
        try:
            type_body = agent.filemanager.filetype(dst)
        except IOError as ex:
            self.log.error(
                "get_archive_file_type: filetype on '%s' failed with: %s",
                            dst, str(ex))
            raise IOError("Filetype on '%s' failed with: %s" % (dst, str(ex)))

        if type_body['type'] == 'ZIP':
            file_type = 'zip'
        elif type_body['signature'][0] == ord('<') and \
                           type_body['signature'][1] == ord('?') and \
                           type_body['signature'][2] == ord('x') and \
                           type_body['signature'][3] == ord('m') and \
                           type_body['signature'][4] == ord('l'):
            file_type = 'xml'
        else:
            # dst is unicode
            msg = "file '%s' is an unknown type of " % dst
            msg += "'%s' with an invalid signature: " % type_body['type']
            msg += "%s" % str(type_body['signature'])

            self.log.error("get_archive_type: %s", msg)
            raise IOError(msg)
        return file_type
