import time
import sys
import os
import socket
import datetime

from akiri.framework.api import RESTApplication, DialogPage
from akiri.framework.config import store

from webob import exc

from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm.exc import NoResultFound

from akiri.framework.api import RESTApplication, UserInterfaceRenderer
from akiri.framework.config import store

from akiri.framework.ext.sqlalchemy import meta

from controller.backup import BackupEntry, BackupManager
from controller.agentinfo import AgentInfoEntry, AgentVolumesEntry
from controller.agentstatus import AgentStatusEntry
from controller.domain import Domain

__all__ = ["BackupApplication"]

class BackupApplication(RESTApplication):

    NAME = 'backup'
    DATEFMT = "%I:%M %p PDT on %B %d, %Y"

    def __init__(self, global_conf):
        super(BackupApplication, self).__init__(global_conf)

        domainname = store.get('palette', 'domainname')
        self.domain = Domain.get_by_name(domainname)
        self.telnet_port = store.getint("palette", "telnet_port", default=9000)
        self.telnet_hostname = store.get("palette", "telnet_hostname",
                                         default="localhost")

    def send_cmd(self, cmd):
        # Backup and restore commands are always sent to the primary.
        preamble = "/domainid=%d /type=primary" % (self.domain.domainid)
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((self.telnet_hostname, self.telnet_port))
        conn.send(preamble + ' ' + cmd + '\n')
        print "sent", preamble + ' ' + cmd
        data = conn.recv(3).strip()
        print "got", data
        if data != 'OK':
            # fix me: do something
            print "Bad result back from the controller."
        conn.close()

    def handle_backup(self):
        self.send_cmd("backup")
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

        if displayname:
            self.send_cmd('restore "%s:%s"' % (displayname, backup_entry.name))
        else:
            print >> sys.stderr, \
                "Error: No displayname for volid=%d uuid=%s" % \
                                  (backup_entry.volid, backup_entry.uuid)

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

    def handle_action(self, req):
        action = req.POST['action'].lower()
        if action == 'backup':
            return self.handle_backup()
        elif action == 'restore':
            return self.handle_restore(req)
        raise exc.HTTPBadRequest()

    def handle_set(self, req):
        d = req.POST['set']
        for key in d:
            if key != 'target-location':
                raise exc.HTTPBadRequest("Invalid set key : " + key)

    def handle(self, req):
        if req.method == 'GET':
            domainid = self.domain.domainid
            L = [x.todict(pretty=True) for x \
                     in BackupManager.all(domainid, asc=False)]
            # FIXME: convert TIMEZONE
            tomorrow = datetime.date.today() + datetime.timedelta(days=1)
            midnight = datetime.datetime.combine(tomorrow, datetime.time(0,0))
            scheduled = midnight.strftime(self.DATEFMT)

            options = [{'item': 'Palette Cloud Storage'},
                       {'item': 'On-Premise Storage'}]
            return {
                'config': [{'name': 'archive-backup',
                            'options': options,
                            'value': options[1]['item']}],
                'backups': {'type': 'Production Backups', 'items': L},
                'next': scheduled
                }
        elif req.method == 'POST':
            if 'action' in req.POST and 'set' in req.POST:
                raise exc.HTTPBadRequest("'action' and 'set' are exclusive.")
            if 'action' in req.POST:
                return self.handle_action(req)
            if 'set' in req.POST:
                return self.handle_set(req)
            raise exc.HTTPBadRequest()
        raise exc.HTTPMethodNotAllowed()

class BackupDialog(DialogPage):

    NAME = "backup"
    TEMPLATE = "backup.mako"

    def __init__(self, global_conf):
        super(BackupDialog, self).__init__(global_conf)

        domainname = store.get('palette', 'domainname')
        self.domain = Domain.get_by_name(domainname)

        our_vols = meta.Session.query(AgentStatusEntry).\
            filter(AgentStatusEntry.domainid == self.domain.domainid).\
            subquery()

        query = meta.Session.query(BackupEntry, AgentVolumesEntry).\
            filter(BackupEntry.volid == AgentVolumesEntry.volid).\
            filter(AgentVolumesEntry.volid.has(our_vols)).\
            order_by(BackupEntry.creation_time.desc())

        self.backup_entries = []
        for backup, agent in query.all():
            data = {}
            data['name'] = backup.name
            data['displayname'] = agent.displayname
            data['creation-time'] = str(backup.creation_time)[:19] # Cut off fraction
            self.backup_entries.append(data)

class Backup(UserInterfaceRenderer):

    TEMPLATE = "backup.mako"
    main_active = "backup"

def make_backup(global_conf):
    return Backup(global_conf)
