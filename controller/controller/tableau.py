import logging
import logger
import string
import time
import threading
import platform

from sqlalchemy import Column, Integer, BigInteger, String, DateTime, func
from sqlalchemy.schema import ForeignKey, UniqueConstraint
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from akiri.framework.ext.sqlalchemy import meta

from state import StateManager
from agentmanager import AgentManager
from agent import Agent
from event_control import EventControl

class TableauProcess(meta.Base):
    __tablename__ = 'tableau_processes'

    ###Possible status as reported by "tabadmin status [...]"
    STATUS_RUNNING="RUNNING"
    STATUS_STOPPED="STOPPED"
    STATUS_DEGRADED="DEGRADED"
    STATUS_UNKNOWN="UNKNOWN"

    name = Column(String, nullable=False, primary_key=True)
    agentid = Column(BigInteger, ForeignKey("agent.agentid"), nullable=False,\
      primary_key=True)
    pid = Column(Integer)
    status = Column(String)
    creation_time = Column(DateTime, server_default=func.now())
    modification_time = Column(DateTime, server_default=func.now(), \
      server_onupdate=func.current_timestamp())
    UniqueConstraint('agentid', 'name')

class TableauStatusMonitor(threading.Thread):

    LOGGER_NAME = "status"

    def __init__(self, server, manager):
        super(TableauStatusMonitor, self).__init__()
        self.server = server
        self.config = self.server.config
        self.manager = manager
        self.log = logger.get(self.LOGGER_NAME)
        self.envid = self.server.environment.envid

        self.status_request_interval = self.config.getint('status', \
                                        'status_request_interval', default=10)

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
        """
            Note a session is passed.  When updating the status table,
            we don't want everything to go away (commit) until we've added
            the new entries.
        """

        # FIXME: Need to figure out how to do this in session.query:
        #        DELETE FROM status USING agent
        #          WHERE status.agentid = agent.agentid
        #            AND agent.domainid = self.domainid;
        #
        # This may do it:
        #
        # subq = session.query(TableauProcess).\
        #   join(Agent).\
        #   filter(Agent.domainid == self.domainid).\
        #   subquery()
        #
        # session.query(TableauProcess).\
        #   filter(TableauProcess.agentid,in_(subq)).\
        #   delete()

        meta.Session.query(TableauProcess).delete()

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
        entry = TableauProcess(agentid=agentid, name=name, pid=pid, status=status)
        session.add(entry)

    def get_all_status(self):
        return meta.Session().query(TableauProcess).\
            join(Agent).\
            filter(Agent.envid == self.envid).\
            all()

    def get_reported_status(self):
        try:
            return meta.Session().query(TableauProcess).\
                join(Agent).\
                filter(Agent.envid == self.envid).\
                filter(Agent.agent_type == 'primary').\
                filter(TableauProcess.name == 'Status').\
                one().status
        except NoResultFound, e:
            return StatusEntry.STATUS_UNKNOWN

    def set_main_state(self, status, aconn):
        main_state = self.stateman.get_state()
        if status not in \
            (TableauProcess.STATUS_RUNNING, TableauProcess.STATUS_STOPPED,
                                                TableauProcess.STATUS_DEGRADED):
            self.log.error("Unknown reported status from tableau: %s. " + \
                                        "main_state: %s", status, main_state)
            return  # fixme: do something more drastic than return?

        if main_state == StateManager.STATE_PENDING:
            self.stateman.update(status)
            if status == TableauProcess.STATUS_RUNNING:
                # StateManager calls the state "STARTED"; Tableau calls
                # it "RUNNING".
                self.server.event_control.gen(EventControl.INIT_STATE_STARTED,
                                                                aconn.__dict__)
            elif status == TableauProcess.STATUS_STOPPED:
                self.server.event_control.gen(EventControl.INIT_STATE_STOPPED,
                                                                aconn.__dict__)
            elif status == TableauProcess.STATUS_DEGRADED:
                self.server.event_control.gen(EventControl.INIT_STATE_DEGRADED,
                                                                aconn.__dict__)
            return

        # If the main state was DEGRADED but status isn't DEGRADED any more,
        # update the main state.
        if main_state == StateManager.STATE_DEGRADED and \
                                status != TableauProcess.STATUS_DEGRADED:
            self.stateman.update(status)
            if status == TableauProcess.STATUS_RUNNING:
                # fixme: should we have a unique alert for the transition
                # from DEGRADED to RUNNING instead of this standard
                # "started" alert?
                self.server.event_control.gen(EventControl.STATE_STARTED,
                                              aconn.__dict__)
            elif status == StateManager.STATUS_STOPPED:
                self.server.event_control.gen(EventControl.STATE_STOPPED,
                                              aconn.__dict__)
            else:
                self.log.error("Unexpected transition from DEGRADED to: %s",
                                                                    status)
            return

        # If the main state is wrong, correct it.
        if main_state == StateManager.STATE_STOPPED and \
                                        status == TableauProcess.STATUS_RUNNING:
            self.log.debug("Updating main state to %s", status)
            self.stateman.update(StateManager.STATE_STARTED)
            self.server.event_control.gen(EventControl.STATE_STARTED,
                                          aconn.__dict__)
        elif main_state == StateManager.STATE_STARTED and \
                status == TableauProcess.STATUS_STOPPED:
            self.log.debug("Updating main state to %s", status)
            self.stateman.update(StateManager.STATE_STOPPED)
            self.server.event_control.gen(EventControl.STATE_STOPPED,
                                          aconn.__dict__)
        elif status == TableauProcess.STATUS_DEGRADED and \
                main_state != TableauProcess.STATUS_DEGRADED:
            self.log.debug("Updating main state to %s", status)
            self.stateman.update(StateManager.STATE_DEGRADED)
            self.server.event_control.gen(EventControl.STATE_DEGRADED,
                                                            aconn.__dict__)

    def run(self):
        while True:
            self.log.debug("status-check: About to timeout or wait for a " + \
                                                    "new primary to connect")
            new_primary = self.manager.new_primary_event.wait(\
                                                self.status_request_interval)
            self.log.debug("status-check: new_primary: %s", new_primary)
            if new_primary:
                self.manager.new_primary_event.clear()
            self.check_status()

    def check_status(self):

        # FIXME: Tie agent to domain.
        aconn = self.manager.agent_conn_by_type(AgentManager.AGENT_TYPE_PRIMARY)
        if not aconn:
            session = meta.Session()
            self.log.debug(\
                        "status thread: No primary agent currently connected.")
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

    def get_agent_id_from_host(self, host):
        # FIXME: As an optimization, look in the acon list before looking
        #        in the database.

        # Note: The passed host may be a hostname or an IP address.

        agentid = None;

        # FIXME: Should the caller pass us a session?
        session = meta.Session()

        try:
            entry = session.query(Agent).\
              filter(Agent.hostname == host).\
              one()
            agentid = entry.agentid;
        except NoResultFound, e:
            try:
                entry = session.query(Agent).\
                  filter(Agent.ip_address == host).\
                  one()
                agentid = entry.agentid;
            except NoResultFound, e:
                pass
            except MultipleResultsFound, e:
                # FIXME: log error
                pass
        except MultipleResultsFound, e:
            # FIXME: log error
            pass

        return agentid

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

        session = meta.Session()

        self.remove_all_status()
        # Do not commit until after the table is added to.
        # Otherwise, the table could be empty temporarily.

        system_status = None;
        for line in lines:
            parts = line.strip().split(' ')

            # 'Tableau Server Repository Database' (1764) is running.
            if parts[0] == "'Tableau" and parts[1] == 'Server':
                if agentid:
                    status = parts[-1:][0]     # "running."
                    status = status[:-1]       # "running" (no period)
                    pid_part = parts[-3:-2][0] # "(1764)"
                    pid_str = pid_part[1:-1]   # "1764"
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
                else:
                    # FIXME: log error
                    pass
            elif parts[0] == 'Status:':
                server_status = parts[1].strip()
                if agentid:
                    self.add(agentid, "Status", 0, server_status)
                    if system_status == None or server_status == 'DEGRADED':
                        system_status = server_status
                else:
                    # FIXME: log error
                    pass
            else:
                host = parts[0].strip().replace(':','')
                agentid = self.get_agent_id_from_host(host)

        session.commit()

        self.set_main_state(system_status, aconn)
        self.log.debug("Logging main status: %s", system_status)

        session.commit()

        # debug - try to get it back
        #self.log.debug("--------current status---------------")
        #all_status = self.get_all_status()
        #for status in all_status:
        #    self.log.debug("status: %s (%d) %s", status.name, status.pid,
        #                                                        status.status)
        #
        #reported_status = self.get_reported_status()
        #self.log.debug("reported_status: %s: %s", reported_status.name,
        #                                            reported_status.status)
