import logging
import logger
import string
import time
import threading
import platform

import sqlalchemy
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, func
from sqlalchemy.schema import ForeignKey, UniqueConstraint
import meta

from state import StateManager, StateEntry
from agentmanager import AgentManager
from agentstatus import AgentStatusEntry

class StatusEntry(meta.Base):
    __tablename__ = 'status'

    ###Possible status as reported by "tabadmin status [...]"
    STATUS_RUNNING="RUNNING"
    STATUS_STOPPED="STOPPED"
    STATUS_DEGRADED="DEGRADED"

    # FIXME: Make combination of agentid and name a unique key

    name = Column(String, unique=True, nullable=False, primary_key=True)
    agentid = Column(BigInteger, ForeignKey("agent.agentid"), nullable=False)
    pid = Column(Integer)
    status = Column(String)
    creation_time = Column(DateTime, server_default=func.now())
    modification_time = Column(DateTime, server_default=func.now(), \
      server_onupdate=func.current_timestamp())
    UniqueConstraint('agentid', 'name')

class StatusMonitor(threading.Thread):

    LOGGER_NAME = "status"

    def __init__(self, server, manager):
        super(StatusMonitor, self).__init__()
        self.server = server
        self.config = self.server.config
        self.manager = manager
        self.log = logger.get(self.LOGGER_NAME)
        self.domainid = self.server.domainid

        self.status_request_interval = self.config.getint('status', 'status_request_interval', default=10)

        # Start fresh: status table
        session = meta.Session()
        self.remove_all_status()
        session.commit()

        self.stateman = StateManager(self.server)

        # Start fresh: state table
        #self.stateman.update(StateEntry.STATE_TYPE_MAIN, StateEntry.STATE_MAIN_UNKNOWN)
        # fixme: We could check to see if the user had started
        # a backup or restore?
        #self.stateman.update(StateEntry.STATE_TYPE_BACKUP, StateEntry.STATE_BACKUP_NONE))

    # Remove all entries to get ready for new status info.
    def remove_all_status(self):
        """Note a session is passed.  When updating the status table, we don't
        want everything to go away (commit) until we've added the new entries."""
        # FIXME: Need to figure out how to do this in session.query:
        #        DELETE FROM status USING agent
        #          WHERE status.agentid = agent.agentid
        #            AND agent.domainid = self.domainid;
        #
        # This may do it:
        #
        # subq = session.query(StatusEntry).\
        #   join(AgentStatusEntry).\
        #   filter(AgentStatusEntry.domainid == self.domainid).\
        #   subquery()
        #
        # session.query(StatusEntry).\
        #   filter(StatusEntry.agentid,in_(subq)).\
        #   delete()

        meta.Session.query(StatusEntry).delete()

        # Intentionally don't commit here.  We want the existing
        # rows to be available until the new rows are inserted and
        # committed.

    def add(self, agentid, name, pid, status):
        """Note a session is passed.  When updating the status table, we
        do remove_all_status, then slowly add in the new status before
        doing the commit, so the table is not every empty/building if
        somebody checks it.
        """

        session = meta.Session()
        entry = StatusEntry(agentid=agentid, name=name, pid=pid, status=status)
        session.add(entry)

    def get_all_status(self):
        return meta.Session().query(StatusEntry).\
            join(AgentStatusEntry).\
            filter(AgentStatusEntry.domainid == self.domainid).\
            all()

    def get_reported_status(self):
        return meta.Session().query(StatusEntry).\
            join(AgentStatusEntry).\
            filter(AgentStatusEntry.domainid == self.domainid).\
            filter(StatusEntry.name == 'Status').\
            one().status

    def set_main_state(self, status):
        main_state = self.stateman.get_state()
        if status not in ("RUNNING", "STOPPED", "DEGRADED"):
            self.log.error("Unknown reported state: %s with status: %s",\
                                main_state, status)

        if status == "RUNNING":
            # tabadmin calls it "RUNNING", statemanager calls it "STARTED"
            status = StateEntry.STATE_STARTED
        if main_state == StateEntry.STATE_PENDING:
            self.stateman.update(status)
            return

        # If the main state is wrong, correct it.
        if main_state == StateEntry.STATE_STOPPED and status == 'RUNNING':
            self.stateman.update(StateEntry.STATE_STARTED)
        elif main_state == StateEntry.STATE_STARTED and status == 'STOPPED':
            self.stateman.update(StateEntry.STATE_STOPPED)

    def run(self):
        while True:
            self.log.debug("status-check: About to timeout or wait for a new primary to connect")
            new_primary = self.manager.new_primary_event.wait(self.status_request_interval)
            self.log.debug("status-check: new_primary: %s", new_primary)
            if new_primary:
                self.manager.new_primary_event.clear()
            self.check_status()

    def check_status(self):

        # FIXME: Tie agent to domain.
        aconn = self.manager.agent_conn_by_type(AgentManager.AGENT_TYPE_PRIMARY)
        if not aconn:
            session = meta.Session()
            self.log.debug("status thread: No primary agent currently connected.")
            self.remove_all_status()
            session.commit()
            return

        # Don't do a 'tabadmin status -v' if the user is doing an action.
        acquired = aconn.user_action_lock(blocking=False)
        if not acquired:
            self.log.debug(\
                "status thread: Primary agent locked for user action. " + \
                "Skipping status check.")
            return

        # We don't force the user to delay starting their request
        # until the 'tabadmin status -v' is finished.
        aconn.user_action_unlock()

        self.check_status_with_connection(aconn)

    def check_status_with_connection(self, aconn):
        agentid = aconn.agentid

        body = self.server.status_cmd(aconn)
        if not body.has_key('stdout'):
            # fixme: Probably update the status table to say something's wrong.
            self.log.error(\
                    "No output received for status monitor. body:" + str(body))
            return

        body = body['stdout']
        lines = string.split(body, '\n')

        if len(lines) < 1:
            # fixme: Probably update the status table to say something's wrong.
            self.log.error("Bad status returned.  Too few lines.")
            return

        # Find the line beginning with "Status:".
        status = None
        skip = 0
        for line in lines:
            parts = line.strip().split(' ')
            skip = skip + 1
            if parts[0] == 'Status:':
                status = parts[1].strip()
                break;
        if status == None:
            self.log.error("Bad status returned: no Tableau status line: " + \
              str(lines))
            return
        if status == 'STOPPED':
            skip = len(lines)

        session = meta.Session()

        # Store the second part (like "RUNNING") into the database
        self.remove_all_status()
        self.add(agentid, "Status", 0, status)
        self.log.debug("Logging main status: %s", status)
        session.commit()

        # Set the "main status" state according to the current status.
        self.set_main_state(status)

        for line in lines[skip:]:   # Skip the first line we already did.
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

            self.add(agentid, name, pid, status)
            self.log.debug("logged: %s, %d, %s", name, pid, status)

        session.commit()

        return    # no debugging for now
        # debug - try to get it back
        self.log.debug("--------current status---------------")
        all_status = self.get_all_status()
        for status in all_status:
            self.log.debug("status: %s (%d) %s", status.name, status.pid,
                                                                status.status)

        reported_status = self.get_reported_status()
        self.log.debug("reported_status: %s: %s", reported_status.name,
                                                    reported_status.status)
