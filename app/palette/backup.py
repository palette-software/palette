import time
import sys

from webob import exc

from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import sessionmaker
import meta

from akiri.framework.api import RESTApplication

from . import Session

__all__ = ["BackupApplication"]

class BackupEntry(meta.Base):
    __tablename__ = 'backup'

    name = Column(String, primary_key=True)
    ip_address = Column(String)
    creation_time = Column(DateTime, default=func.now())

    def __init__(self, name, ip_address):
        self.name = name
        self.ip_address = ip_address

class BackupApplication(RESTApplication):

    NAME = 'backup'

    scheduled = 'Thursday, November 7 at 12:00 AM'

    def handle_backup(self):
        now = time.strftime('%A, %B %d at %I:%M %p')
        return {'last': now,
                'next': self.scheduled }

    def handle_restore(self):
        now = time.strftime('%A, %B %d at %I:%M %p')
        return {'last': now,
                'next': self.scheduled }


    def handle(self, req):
        if req.method == 'GET':
            db_session = Session()
            last_db = db_session.query(BackupEntry).first()
            if not last_db:
                last = "No backups done."
            else:
                last = str(last_db.creation_time)

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
