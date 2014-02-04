import sqlalchemy
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import sessionmaker
import meta
import sys

from akiri.framework.api import RESTApplication, DialogPage

from . import Session

__all__ = ["MonitorApplication"]

class MonitorApplication(RESTApplication):

    NAME = 'monitor'

    def handle(self, req):
        db_session = Session()
        self.status_entries = db_session.query(StatusEntry).all()

        # Dig out the main status and time
        main_status = "Unknown"
        for entry in self.status_entries:
            if entry.name == 'Status':
                self.main_status = entry.status
        if main_status == 'Running':
            return {'status': 'OK'}
        else:
            return {'status': 'Fault Status'}

class StatusEntry(meta.Base):
    __tablename__ = 'status'

    name = Column(String, primary_key=True)
    pid = Column(Integer)
    status = Column(String)
    creation_time = Column(DateTime, default=func.now())

    def __init__(self, name, pid, status):
        self.name = name
        self.pid = pid
        self.status = status

class StatusDialog(DialogPage):

    NAME = "status"
    TEMPLATE = "status.mako"

    def __init__(self, global_conf):
        super(StatusDialog, self).__init__(global_conf)

        db_session = Session()
        self.status_entries = db_session.query(StatusEntry).all()

        # Dig out the main status and time
        self.main_status = "Unknown"
        self.status_time = "Unknown"
        for entry in self.status_entries:
            if entry.name == 'Status':
                self.main_status = entry.status
                self.status_time = str(entry.creation_time)[:19] # Cut off fraction
