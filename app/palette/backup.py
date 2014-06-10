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

from controller.backup import BackupEntry, BackupManager
from controller.agentinfo import AgentInfoEntry, AgentVolumesEntry
from controller.agentstatus import AgentStatusEntry
from controller.domain import Domain
from controller.util import DATEFMT

from rest import PaletteRESTHandler, required_parameters

__all__ = ["BackupApplication"]

class BackupApplication(PaletteRESTHandler):

    NAME = 'backup'

    def handle_backup(self):
        self.telnet.send_cmd("backup")
        now = time.strftime('%A, %B %d at %I:%M %p')
        return {'last': now }

    def handle_restore(self, req):
        if not 'filename' in req.POST:
            print >> sys.stderr, "Missing filename.  Ignoring backup request."
            return {}

        filename = req.POST['filename']

        backup_entry = self.get_backup_entry_from_backup_name(filename)
        if not backup_entry:
            print >> sys.stderr, "Backup not found:", filename
            return {}

        displayname = self.get_displayname_by_volid(backup_entry.volid)
        if not displayname:
            print >> sys.stderr, \
                "Error: No displayname for volid=%d uuid=%s" % \
                                  (backup_entry.volid, backup_entry.uuid)
            return {}

        vol_entry = AgentVolumesEntry.get_vol_entry_by_volid(backup_entry.volid)
        if not vol_entry:
            print >> sys.stderr, \
                "Error: No vol_entry for volid=%d uuid=%s" % \
                                  (backup_entry.volid, backup_entry.uuid)
            return {}

        self.telnet.send_cmd('restore "%s:%s/%s"' % \
                (displayname, vol_entry.name, backup_entry.name))

        return {}

    def get_backup_entry_from_backup_name(self, name):
        try:
            entry = meta.Session.query(BackupEntry).\
                filter(BackupEntry.name == name).\
                one()
        except NoResultFound, e:
            return None

        return entry

    def get_displayname_by_volid(self, volid):
        try:
            agent_entry, vol_entry = meta.Session.query(\
                AgentStatusEntry, AgentVolumesEntry).\
                filter(AgentStatusEntry.agentid == AgentVolumesEntry.agentid).\
                filter(AgentVolumesEntry.volid == volid).\
                one()
        except NoResultFound, e:
            return None

        return agent_entry.displayname

    def get_last_backup(self):
        last_db = meta.Session.query(BackupEntry).\
            order_by(BackupEntry.creation_time.desc()).\
            first()
        return last_db

    @required_parameters('action')
    def handle_POST(self, req):
        action = req.POST['action'].lower()
        if action == 'backup':
            return self.handle_backup()
        elif action == 'restore':
            return self.handle_restore(req)
        raise exc.HTTPBadRequest()

    @required_parameters('value')
    def handle_archive_POST(self, req):
        self.system.save('archive-location', req.POST['value'])
        meta.Session.commit()
        return {}

    def handle_GET(self, req):
        L = [x.todict(pretty=True) for x \
                 in BackupManager.all(self.domain.domainid, asc=False)]
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
            'backups': {'type': 'Production Backups', 'items': L},
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
