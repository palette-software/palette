import time
import sys
import os
import socket
import datetime

from webob import exc

from akiri.framework.config import store

from sqlalchemy.orm.exc import NoResultFound

from akiri.framework.config import store
from akiri.framework.ext.sqlalchemy import meta

from controller.files import FileEntry, FileManager
from controller.agentinfo import AgentVolumesEntry
from controller.agent import Agent
from controller.domain import Domain
from controller.util import DATEFMT
from controller.profile import Role

from rest import PaletteRESTHandler, required_parameters, required_role

__all__ = ["BackupApplication"]

class BackupApplication(PaletteRESTHandler):

    NAME = 'backup'

    @required_role(Role.MANAGER_ADMIN)
    def handle_backup(self, req):
        self.telnet.send_cmd("backup", req=req)
        now = time.strftime('%A, %B %d at %I:%M %p')
        return {'last': now }

    @required_role(Role.MANAGER_ADMIN)
    def handle_restore(self, req):
        if not 'filename' in req.POST:
            print >> sys.stderr, "Missing filename.  Ignoring backup request."
            return {}

        filename = req.POST['filename']

        backup_entry = FileManager.find_by_name_envid(req.envid, filename)
        if not backup_entry:
            print >> sys.stderr, "Backup not found:", filename
            return {}

        self.telnet.send_cmd('restore "%s"' % backup_entry.name, req=req)
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
    def handle_archive_POST(self, req):
        value = req.POST['value']
        self.system.save('archive-location', value)
        return {'value':value}

    @required_role(Role.READONLY_ADMIN)
    def handle_GET(self, req):
        L = [x.todict(pretty=True) for x \
                 in FileManager.all(req.envid,
                                    FileManager.FILE_TYPE_BACKUP,
                                    asc=False)]
        # FIXME: convert TIMEZONE
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        midnight = datetime.datetime.combine(tomorrow, datetime.time(0,0))
        scheduled = midnight.strftime(DATEFMT)

        options = [{'item': 'Palette Cloud Storage'},
                   {'item': 'On-Premise Storage'}]
        return {
            'config': [{'name': 'archive-backup',
                        'options': options,
                        'value': options[1]['item']}],
            'backups': {'type': 'Restore From', 'items': L},
            'next': scheduled
            }

    def handle(self, req):
        path_info = self.base_path_info(req)
        if path_info == '':
            if req.method == 'GET':
                return self.handle_GET(req)
            elif req.method == 'POST':
                return self.handle_POST(req)
            raise exc.HTTPMethodNotAllowed()
        elif path_info == 'location':
            if req.method == 'POST':
                return self.handle_archive_POST(req)
            raise exc.HTTPMethodNotAllowed()
        raise exc.HTTPBadRequest()
