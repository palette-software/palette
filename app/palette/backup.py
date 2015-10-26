import time
import datetime

from webob import exc

from akiri.framework import ENVIRON_PREFIX

from controller.files import FileManager
from controller.util import DATEFMT
from controller.profile import Role
from controller.tz import tzlocal

from .rest import required_parameters, required_role, PaletteRESTApplication

class BackupApplication(PaletteRESTApplication):
    """Base backup application used by the API"""
    MAX_LIMIT = 100

    def _backup_entries(self, envid, limit=None, desc=True):
        """Return a list of backup entries sorted by filename
           - sorting by filename is the same as sorting by date.
        """
        file_type = FileManager.FILE_TYPE_BACKUP
        return FileManager.all_by_type(envid, file_type,
                                       asc=(not desc), limit=limit)

    def _backup_asdict(self, entry):
        """ Convert to API naming
        FIXME: this can be removed when the UI uses this interface.
        """
        return entry.api()

    def service_one_backup(self, req, fileid):
        """Return information about a particular backup."""
        # pylint: disable=unused-argument
        entry = FileManager.find_by_fileid(fileid)
        if entry is None:
            raise exc.HTTPNotFound()
        data = self._backup_asdict(entry)
        data['status'] = 'OK'
        return data

    @required_role(Role.READONLY_ADMIN)
    def service_GET(self, req):
        key = ENVIRON_PREFIX + 'id'
        if key in req.environ:
            return self.service_one_backup(req, req.environ[key])

        desc = req.params_getbool('desc', default=True)
        limit = req.params_getint('limit', default=self.MAX_LIMIT)
        backups = []
        for entry in self._backup_entries(req.envid, limit=limit, desc=desc):
            backups.append(self._backup_asdict(entry))
        return {'status': 'OK', 'backups': backups}

class RestoreMixin(object):
    """Mixin to add the 'restore' manage action."""

    @required_role(Role.MANAGER_ADMIN)
    def handle_restore(self, req):
        """Do a Tableau restore using a given filename."""
        sync = req.params_getbool('sync', default=False)

        # FIXME: merge...
        if 'url' in req.POST:
            cmd = 'restore-url "%s"' % req.POST['url']
        elif 'filename' in req.POST:
            filename = req.POST['filename']

            backup_entry = FileManager.find_by_name_envid(req.envid, filename)
            if not backup_entry:
                return {'status': 'FAILED',
                        'error': 'Backup not found: ' + filename}
            cmd = 'restore "%s"' % backup_entry.name
        else:
            raise exc.HTTPBadRequest("Either 'url' or 'filename' is required.")

        password = req.params_get('password', default=None)
        if password:
            cmd += ' "%s"' % password

        restore_type = req.params_get('restore-type', default=None)
        if restore_type and restore_type.lower() == 'data-only':
            # FIXME: make the UX use the 'data-only' key
            cmd = '/noconfig ' + cmd
        elif req.params_getbool('data-only', default=False):
            cmd = '/noconfig ' + cmd

        # These are silently ignored by restore-url
        if not req.params_getbool('backup', default=False):
            cmd = '/nobackup ' + cmd
        if not req.params_getbool('license', default=False):
            cmd = '/nolicense ' + cmd

        self.commapp.send_cmd(cmd, req=req, read_response=sync)
        return {'status': 'OK'}


class BackupRestoreApplication(BackupApplication, RestoreMixin):
    """Extended backup application used by the UI"""

    def _backup_asdict(self, entry):
        """ Convert to API naming
        FIXME: this can be removed when the UI uses the API interface.
        """
        return entry.todict(pretty=True)

    @required_role(Role.MANAGER_ADMIN)
    def handle_backup(self, req):
        self.commapp.send_cmd("backup", req=req, read_response=False)
        now = time.strftime('%A, %B %d at %I:%M %p')
        return {'last': now}

    @required_parameters('action')
    def handle_POST(self, req):
        action = req.POST['action'].lower()
        if action == 'backup':
            return self.handle_backup(req)
        elif action == 'restore':
            return self.handle_restore(req)
        raise exc.HTTPBadRequest()

    @required_role(Role.MANAGER_ADMIN)
    @required_parameters('value')
    # pylint: disable=invalid-name
    def handle_archive_POST(self, req):
        value = req.POST['value']
        req.system.save('archive-location', value)
        return {'value':value}

    @required_role(Role.READONLY_ADMIN)
    def handle_GET(self, req):
        data = super(BackupRestoreApplication, self).service_GET(req)
        items = data['backups']

        # FIXME: convert TIMEZONE
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        midnight = datetime.datetime(tomorrow.year,
                                     tomorrow.month,
                                     tomorrow.day,
                                     0, 0, 0, 0, tzlocal())
        scheduled = midnight.strftime(DATEFMT)

        # FIXME: simplify 'backups'
        return {'backups': {'type': 'Restore From', 'items': items},
                'next': scheduled}

    def service(self, req):
        if 'action' in req.environ:
            action = req.environ['action']
            if action == 'location':
                if req.method == 'POST':
                    return self.handle_archive_POST(req)
                raise exc.HTTPMethodNotAllowed()
            raise exc.HTTPNotFound()

        if req.method == 'GET':
            return self.handle_GET(req)
        elif req.method == 'POST':
            return self.handle_POST(req)
        raise exc.HTTPMethodNotAllowed()
