import time
import sys
import socket

from webob import exc

from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import sessionmaker
import meta

from akiri.framework.api import RESTApplication

from . import Session

from inits import *

__all__ = ["BackupApplication"]

class BackupEntry(meta.Base):
    __tablename__ = 'backup'

    name = Column(String, primary_key=True)
    ip_address = Column(String)
    creation_time = Column(DateTime, default=func.now())

    def __init__(self, name, ip_address, creation_time):
        self.name = name
        self.ip_address = ip_address
        self.creation_time = creation_time

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

        self.send_cmd("restore %s" % last_entry.name)

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
