import logging
import unicodedata

from place_file import PlaceFile
from sites import Site
from profile import UserProfile
from util import success

logger = logging.getLogger()

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
            logger.error("%s archive_file: filemanager.filesize('%s')" +
                         "failed: %s", self.NAME, dst, str(ex))
        else:
            if not success(file_size_body):
                logger.error("%s archive_file: Failed to get size of " + \
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
        logger.debug("%s build filename %s: %s", self.NAME, dst, place.info)

        return place

    def sendevent(self, key, update, error, data):
        """Send the event."""

        if 'embedded' in data:
            del data['embedded']
        if error:
            logger.error(error)
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

    def tabcmd_run(self, agent, update, url, dst, site_id,
                   remove_update_method):
        # pylint: disable=too-many-arguments
        """Does the tabcmd_run to get the datasource or workbook file.
           Returns:
                True:   Returns dst (unchanged)
                False:  Fail
        """

        site_entry = Site.get(self.envid, site_id, default=None)

        if not site_entry:
            logger.error("%s: Missing site id: %d", self.NAME, site_id)
            return {'error': 'Missing site id: %d' % site_id}

        if site_entry.url_namespace:
            site = '--site %s' % site_entry.url_namespace
        else:
            site = ''

        cmd = 'get %s %s -f "%s"' % (url, site, dst)

        logger.debug('building %s archive: %s', self.NAME, dst)

        for _ in range(3):
            body = self.server.tabcmd(cmd, agent)
            if success(body):
                return body

            if 'stderr' not in body:
                continue    # try again

            # It failed and we have stderr.
            if "404" in body['stderr'] and "Not Found" in body['stderr']:
                # The update was deleted before we
                # got to it.  Subsequent attempts will also fail,
                # so delete the update row to stop
                # attempting to retrieve it again.
                remove_update_method(update)
                return body
            elif 'Service Unavailable' in body['stderr']:
                # 503 error, retry
                logger.debug(cmd + ' : 503 Service Unavailable, retrying')
                continue
            else:
                # It failed for another reason. Don't try again now.
                return body

        return body
