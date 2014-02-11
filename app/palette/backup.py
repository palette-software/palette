import time
import sys
import os
import socket

from akiri.framework.api import RESTApplication, DialogPage

from webob import exc

from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
import meta

from akiri.framework.api import RESTApplication

from . import Session

from inits import *
from controller.backup import BackupEntry
from controller.agentstatus import AgentStatusEntry

__all__ = ["BackupApplication"]

class BackupApplication(RESTApplication):

    NAME = 'backup'

    scheduled = 'Thursday, November 7 at 12:00 AM'

    def send_cmd(self, cmd):
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect(("", CONTROLLER_TELNET_PORT))
        conn.send(cmd + '\n')
        print "sent", cmd
        data = conn.recv(3).strip()
        print "got", data
        if data != 'OK':
            # fix me: do something
            print "Bad result back from the controller."
        conn.close()

    def handle_backup(self):
        self.send_cmd("backup")
        now = time.strftime('%A, %B %d at %I:%M %p')
        return {'last': now,
                'next': self.scheduled }

    def handle_restore(self):
        last_entry = self.get_last_backup()
        if not last_entry:
            print >> sys.syserr, "No backups to restore from!"
            return {'last': "none",
                    'next': self.scheduled }

        hostname = self.get_hostname_by_uuid(last_entry.uuid)

        if hostname:
            self.send_cmd("restore %s:%s" % (hostname, last_entry.name))
        else:
            print "Error: Not agent with uuid:", last_entry.uuid

    def get_hostname_by_uuid(self, uuid):
        db_session = Session()
        try:
            query = db_session.query(AgentStatusEntry, BackupEntry)
            agent_entry = query.filter(\
                AgentStatusEntry.uuid == BackupEntry.uuid).\
                first()

        except NoResultFound, e:
            return None
        finally:
            db_session.close()

        return agent_entry[0].hostname

    def get_last_backup(self):
        db_session = Session()
        last_db = db_session.query(BackupEntry).\
            order_by(BackupEntry.creation_time.desc()).\
            first()
        db_session.close()
        return last_db

    def handle(self, req):
        if req.method == 'GET':
            last_entry = self.get_last_backup()
            if not last_entry:
                last = "No backups done."
            else:
                last = str(last_entry.creation_time)

            return {'last': last,
                    'next': self.scheduled}
        elif req.method == 'POST':
            if 'action' not in req.POST:
                raise exc.HTTPBadRequest()
            action = req.POST['action'].lower()
            if action == 'backup':
                return self.handle_backup()
            elif action == 'restore':
                return self.handle_restore()
            raise exc.HTTPBadRequest()
        raise exc.HTTPMethodNotAllowed()

class BackupDialog(DialogPage):

    NAME = "backup"
    TEMPLATE = "backup.mako"

    def __init__(self, global_conf):
        super(BackupDialog, self).__init__(global_conf)

    def __init__(self, global_conf):
        super(BackupDialog, self).__init__(global_conf)

        db_session = Session()
        self.backup_entries = db_session.query(BackupEntry).all()
        for entry in self.backup_entries:
            entry.creation_time = str(entry.creation_time)[:19] # Cut off fraction
        db_session.close()
