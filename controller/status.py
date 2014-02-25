import logging
import logger
import string
import time
import threading
import platform

import sqlalchemy
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, func
from sqlalchemy.schema import ForeignKey, UniqueConstraint
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
import meta

from state import StateManager
from inits import *

class StatusEntry(meta.Base):
    __tablename__ = 'status'

    # FIXME: Make combination of agentid and name a unique key

    name = Column(String, unique=True, nullable=False, primary_key=True)
    agentid = Column(BigInteger, ForeignKey("agents.agentid"), nullable=False)
    pid = Column(Integer)
    status = Column(String)
    creation_time = Column(DateTime, default=func.now(), \
      onupdate=func.current_timestamp())
    UniqueConstraint('agentid', 'name')

    def __init__(self, agentid, name, pid, status):
        self.agentid = agentid
        self.name = name
        self.pid = pid
        self.status = status

class StatusMonitor(threading.Thread):

    LOGGER_NAME = "status"

    def __init__(self, server, manager):
        super(StatusMonitor, self).__init__()
        self.server = server
        self.config = self.server.config
        self.manager = manager
        self.log = logger.get(self.LOGGER_NAME)

        self.status_request_interval = self.config.getint('status', 'status_request_interval', default=10)

        self.Session = sessionmaker(bind=meta.engine)
        
        # Start fresh: status table
        session = self.Session()
        self.remove_all_status(session)
        session.commit()
        session.close()

        self.stateman = StateManager(self.server)

        # Start fresh: state table
        #self.stateman.update(STATE_TYPE_MAIN, STATE_MAIN_UNKNOWN)
        # fixme: We could check to see if the user had started
        # a backup or restore?
        #self.stateman.update(STATE_TYPE_SECOND, STATE_SECOND_NONE)

    # Remove all entries to get ready for new status info.
    def remove_all_status(self, session):
        """Note a session is passed.  When updating the status table, we don't
        want everything to go away (commit) until we've added the new entries."""
        session.query(StatusEntry).\
            delete()

        # Intentionally don't commit here.  We want the existing
        # rows to be available until the new rows are inserted and
        # committed.

    def add(self, session, agentid, name, pid, status):
        """Note a session is passed.  When updating the status table, we do
        remove_all_status, then slowly add in the new status before doing the commit,
        so the table is not every empty/building if somebody checks it."""
        entry = StatusEntry(agentid, name, pid, status)
        session.add(entry)

    def get_all_status(self):
        session = self.Session()
        status_entries = session.query(StatusEntry).all()
        session.close()
        return status_entries

    def get_main_status(self):
        session = self.Session()
        main_status = session.query(StatusEntry).\
            filter(StatusEntry.name == 'Status').one()
        session.close()
        return main_status

    def set_main_state(self, status):
        """Set main_state if appropriate."""

        states = self.stateman.get_states()
        main_state = states[STATE_TYPE_MAIN]

        if status == "RUNNING":
            if main_state == STATE_MAIN_STARTING or \
                                        main_state == STATE_MAIN_UNKNOWN:
                self.stateman.update(STATE_TYPE_MAIN, STATE_MAIN_STARTED)
                self.log.debug("Updated state table with main status: %s", STATE_MAIN_STARTED)
            elif main_state == 'STOPPED':
                # This shouldn't happen.
                self.log.error("Unexpected Status! Status is RUNNING but main_state was STOPPED!")
            elif main_state == STATE_MAIN_STARTED or \
                                        main_state == STATE_MAIN_STOPPING:
                # Don't change the state.
                pass
            else:
                self.log.error("Unexpected main state: %s with status: %s", main_state, status)

        elif status == 'STOPPED':
            if main_state == STATE_MAIN_STOPPING or \
                                    main_state == STATE_MAIN_UNKNOWN:
                self.stateman.update(STATE_TYPE_MAIN, STATE_MAIN_STOPPED)
                self.log.debug("Updated state table with main status: %s", STATE_MAIN_STOPPED)

                if main_state == STATE_MAIN_UNKNOWN:
                    # If we are transitioning from UNKNOWN to STOPPED, then
                    # send a "maint start" command to the agent.
                    return    # return here to skip 'maint start'
                    self.log.info("Sending 'maint start' command for transition from STATE_MAIN_UNKNOWN to STATE_MAIN_STOPPED")
                    maint_body = self.server.maint("start")
                    if maint_body.has_key("error"):
                        self.log.error("set_main_state: 'maint start' failed after transition from STATE_MAIN_UNKNOWN to STATE_MAIN_STOPPED: " + maint_body['error'])

            elif main_state == STATE_MAIN_STARTING or \
                                        main_state == STATE_MAIN_STOPPED:
                # don't change the state.
                pass
            elif main_state == STATE_MAIN_STARTED:
                self.log.error("Unexpected Status! Status is STOPPED but main_state was STARTED!")
            else:
                self.log.error("Unexpected main state %s with status %s", main_state, status)

        elif status == 'DEGRADED':
                # fixme: do anything for this?
                pass
        else:
            self.log.error("Unknown status: %s", status)

    def run(self):
        session = self.Session()
        while True:
            self.check_status(session)
            time.sleep(self.status_request_interval)

    def check_status(self, session):

        aconn = self.manager.agent_conn_by_type(AGENT_TYPE_PRIMARY)
        if not aconn:
            self.log.debug("status thread: No primary agent currently connected.")
            self.remove_all_status(session)
            session.commit()
            return
        agentid = aconn.agentid

        body = self.server.status_cmd(aconn)
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
            self.log.error("Status returned: " + str(lines))
            return

        status = line1[1]

        # Store the second part (like "RUNNING") into the database
        self.remove_all_status(session)
        self.add(session, agentid, "Status", 0, status)
        self.log.debug("Logging main status: %s", status)
        session.commit()

        # Set the "main status" state according to the current status.
        self.set_main_state(status)

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
            
            self.add(session, agentid, name, pid, status)
            self.log.debug("logged: %s, %d, %s", name, pid, status)

        session.commit()

        return    # no debugging for now
        # debug - try to get it back
        self.log.debug("--------current status---------------")
        all_status = self.get_all_status()
        for status in all_status:
            self.log.debug("status: %s (%d) %s", status.name, status.pid, status.status)

        main_status = self.get_main_status()
        self.log.debug("main_status: %s: %s", main_status.name, main_status.status)
