import time
import sys
import datetime
from dateutil.tz import tzlocal

from webob import exc

from controller.files import FileManager
from controller.util import DATEFMT
from controller.profile import Role

from .rest import required_parameters, required_role, PaletteRESTApplication

__all__ = ["BackupApplication"]

class BackupApplication(PaletteRESTApplication):

    @required_role(Role.MANAGER_ADMIN)
    def handle_backup(self, req):
        self.commapp.send_cmd("backup", req=req, read_response=False)
        now = time.strftime('%A, %B %d at %I:%M %p')
        return {'last': now}

    @required_parameters('filename', 'backup', 'license')
    @required_role(Role.MANAGER_ADMIN)
    def handle_restore(self, req):

        filename = req.POST['filename']

        backup_entry = FileManager.find_by_name_envid(req.envid, filename)
        if not backup_entry:
            return {'error': 'Backup not found: ' + filename }

        cmd = 'restore "%s"' % backup_entry.name

        if 'password' in req.POST and len(req.POST['password']):
            cmd += ' "%s"' % req.POST['password']

        if req.POST['restore-type'] == 'data-only':
            cmd = '/no-config ' + cmd

        if not req.params_getbool('backup'):
            cmd = cmd + ' nobackup'
        if not req.params_getbool('license'):
            cmd = cmd + ' nolicense'

        print >> sys.stderr, cmd
        return {}

        self.commapp.send_cmd(cmd, req=req, read_response=False)
        return {}

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
        items = [x.todict(pretty=True) for x \
                 in FileManager.all_by_type(req.envid,
                                            FileManager.FILE_TYPE_BACKUP,
                                            asc=False)]
        # FIXME: convert TIMEZONE
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        midnight = datetime.datetime(tomorrow.year,
                                     tomorrow.month,
                                     tomorrow.day,
                                     0, 0, 0, 0, tzlocal())
        scheduled = midnight.strftime(DATEFMT)

        options = [{'item': 'Palette Cloud Storage'},
                   {'item': 'On-Premise Storage'}]
        return {
            'config': [{'name': 'archive-backup',
                        'options': options,
                        'value': options[1]['item']}],
            'backups': {'type': 'Restore From', 'items': items},
            'next': scheduled
            }

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
