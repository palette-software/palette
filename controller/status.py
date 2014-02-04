import logging
import logger
import string
import time
import threading
import platform

import sqlalchemy
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.schema import ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
import meta

from inits import *
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

class StatusMonitor(threading.Thread):

    def __init__(self, server, manager):
        super(StatusMonitor, self).__init__()
        self.server = server
        self.manager = manager
        self.log = logger.config_logging(STATUS_LOGGER_NAME, logging.INFO)
#        self.log = logger.config_logging(STATUS_LOGGER_NAME, logging.DEBUG)

        # fixme: move to .ini config file
        if platform.system() == 'Windows':
            # Windows with Tableau uses port 8060
            url = "postgresql://palette:palpass:8060@localhost/paldb"
        else:
            url = "postgresql://palette:palpass@localhost/paldb"

        self.engine = sqlalchemy.create_engine(url, echo=False)

        meta.Base.metadata.create_all(bind=self.engine)
        
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    # Remove all entries to get ready for new status info.
    def remove_all_status(self):
        self.session.query(StatusEntry).\
            delete()

    def get_all_status(self):
        status_entries = self.session.query(StatusEntry).all()
        return status_entries

    def get_main_status(self):
        main_status = self.session.query(StatusEntry).\
            filter(StatusEntry.name == 'Status').one()
        return main_status

    def add(self, name, pid, status):
        entry = StatusEntry(name, pid, status)
        self.session.add(entry)

    def run(self):
        while True:
            time.sleep(DEFAULT_STATUS_SLEEP_INTERVAL)
            self.check_status()

    def check_status(self):

        if not self.manager.agent_handle(AGENT_TYPE_PRIMARY):
            self.log.debug("status thread: No primary agent currently connected.")
            return

        body = self.server.status_cmd()
        if not body.has_key('stdout'):
            # fixme: Probably update the status table to say something's wrong.
            self.log.error("No output received for status monitor. body:" + str(body))
            return

        body = body['stdout']
        lines = string.split(body, '\n')
        if len(lines) < 1:
            self.log.error("Bad status returned.  Too few lines.")
            return

        if len(lines) == 1:
            # "Status: STOPPED" is the only line
            line1 = body.split(" ")
        else:
            # "Status: RUNNING"
            line1 = lines[0].split(" ")

        if line1[0] != 'Status:':
            self.log.error("Bad status returned.  First line wasn't 'Status:' %s:", line1)
            return

        # Store the second part (like "RUNNING") into the database

        self.remove_all_status()

        self.add("Status", 0, line1[1])
        self.log.debug("Logging main status: %s", line1[1])

        for line in lines[1:]:   # Skip the first line we already did.
            line = line.strip()
            if len(line) == 0:
                self.log.debug("Ignoring line due to 0 length")
                continue

            parts = line.split(' ')

            # 'Tableau Server Repository Database' (1764) is running.
            if parts[0] != "'Tableau" or parts[1] != 'Server':
                self.log.error("Bad status line, ignoring: " + parts[0])
                continue

            status = parts[-1:][0]      # "running."
            status = status[:-1]         # "running" (no period)
            pid_part = parts[-3:-2][0]  # "(1764)"
            pid_str = pid_part[1:-1]        # "1764"
            try:
                pid = int(pid_str)
            except:
                self.log.error("Bad PID: " + pid_str)
                continue

            del parts[0:2]  # Remove 'Tableau' and 'Server'
            del parts[-3:]  # Remove ['(1764)', 'is', 'running.']

            name = ' '.join(parts)  # "Repository Database'"
            if name[-1:] == "'":
                name = name[:-1]    # Cut off trailing single quote (')
            
            self.add(name, pid, status)
            self.log.debug("logged: %s, %d, %s", name, pid, status)

        self.session.commit()

        # debug - try to get it back
        self.log.debug("--------current status---------------")
        all_status = self.get_all_status()
        for status in all_status:
            self.log.debug("status: %s (%d) %s", status.name, status.pid, status.status)

        main_status = self.get_main_status()
        self.log.debug("main_status: %s: %s", main_status.name, main_status.status)
