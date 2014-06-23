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
from controller.agentinfo import AgentVolumesEntry
from controller.agent import Agent
from controller.domain import Domain
from controller.util import DATEFMT
from controller.gcs import GCS
from controller.profile import Role

from rest import PaletteRESTHandler, required_parameters, required_role

__all__ = ["BackupApplication"]

class BackupApplication(PaletteRESTHandler):

    NAME = 'backup'

    @required_role(Role.MANAGER_ADMIN)
    def handle_backup(self, req):
        self.telnet.send_cmd("backup")
        now = time.strftime('%A, %B %d at %I:%M %p')
        return {'last': now }

    @required_role(Role.MANAGER_ADMIN)
    def handle_restore(self, req):
        if not 'filename' in req.POST:
            print >> sys.stderr, "Missing filename.  Ignoring backup request."
            return {}

        filename = req.POST['filename']

        backup_entry = self.get_backup_entry_from_backup_name(filename)
        if not backup_entry:
            print >> sys.stderr, "Backup not found:", filename
            return {}

        if backup_entry.volid:
            return self.handle_restore_from_vol(backup_entry)
        elif backup_entry.gcsid:
            return self.handle_restore_from_gcs(backup_entry)
        else:
            print >> sys.stderr, \
                "Error: Don't yet support backup from S3."
            return {}

    def handle_restore_from_gcs(self, backup_entry):
        gcs_entry = GCS.get_by_gcsid_envid(backup_entry.gcsid,
                                                    self.environment.envid)
        if not gcs_entry:
            print >> sys.stderr, \
                "Error: gcsid entry from backup not found for gcsid", \
                                                    backup_entry.gcsid
            return {}

        self.telnet.send_cmd('restore "%s:%s"' % 
                                (gcs_entry.name, backup_entry.name))
        return {}

    def handle_restore_from_vol(self, backup_entry):
        """The backup is on a volume (not gcs or S3)."""
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
                Agent, AgentVolumesEntry).\
                filter(Agent.agentid == AgentVolumesEntry.agentid).\
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
            return self.handle_backup(req)
        elif action == 'restore':
            return self.handle_restore(req)
        raise exc.HTTPBadRequest()

    @required_role(Role.MANAGER_ADMIN)
    @required_parameters('value')
    def handle_archive_POST(self, req):
        self.system.save('archive-location', req.POST['value'])
        meta.Session.commit()
        return {}

    @required_role(Role.READONLY_ADMIN)
    def handle_GET(self, req):
        L = [x.todict(pretty=True) for x \
                 in BackupManager.all(self.environment.envid, asc=False)]
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
