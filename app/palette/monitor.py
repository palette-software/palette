import sqlalchemy
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, func
from sqlalchemy.orm.exc import NoResultFound
import sys

from akiri.framework.api import RESTApplication, DialogPage
from akiri.framework.config import store

from controller import meta
from controller.status import StatusEntry
from controller.state import StateEntry
from controller.backup import BackupEntry
from controller.agentstatus import AgentStatusEntry
from controller.domain import Domain

__all__ = ["MonitorApplication"]

# State types:
STATE_TYPE_MAIN="main"
STATE_TYPE_SECOND="second"

class MonitorApplication(RESTApplication):

    NAME = 'monitor'

    def __init__(self, global_conf):
        super(MonitorApplication, self).__init__(global_conf)
        self.Session = sessionmaker(meta.engine)

        domainname = store.get('palette', 'domainname')
        self.domain = Domain.get_by_name(domainname, Session=self.Session)

    def handle(self, req):
        session = self.Session()

        tableau_status = "Unknown"
        main_state = "Not connected"
        secondary_state = "none"

        try:
            primary_agents = session.query(AgentStatusEntry).\
                filter(AgentStatusEntry.domainid == self.domain.domainid).\
                filter(AgentStatusEntry.agent_type == "primary").\
                all()
        except NoResultFound, e:
            primary_agents = None

        # If there is more than one primary agent in the table, look for
        # the primary agent that is connected and use that.
        # the table.

        primary = None

        if primary_agents:
            for agent in primary_agents:
                if agent.connected():
                    # This primary agent is connected.  We will use it.
                    primary = agent
                    break
                else:
                    # This agent has disconnected.
                    continue

        # If there is a primary agent connected, get tableau status,
        # main, and secondary states.
        if primary:
            # Dig out the tableau status.
            try:
                tableau_entry = session.query(StatusEntry).\
                    join(AgentStatusEntry).\
                    filter(AgentStatusEntry.domainid == self.domain.domainid).\
                    filter(StatusEntry.name == 'Status').\
                    one()
                tableau_status = tableau_entry.status
            except NoResultFound, e:
                pass

            # Dig out the states
            state_entries = session.query(StateEntry).\
                filter(AgentStatusEntry.domainid == self.domain.domainid).\
                all()

            for state_entry in state_entries:
                if state_entry.state_type == STATE_TYPE_MAIN:
                    main_state = state_entry.state
                elif state_entry.state_type == STATE_TYPE_SECOND:
                    secondary_state = state_entry.state
                else:
                    print "monitor: Uknown state_type:", state_entry.state_type

        # Dig out the last/most recent backup.
        last_db = session.query(BackupEntry).\
            join(AgentStatusEntry).\
            filter(AgentStatusEntry.domainid == self.domain.domainid).\
            filter(StatusEntry.name == 'Status').\
            order_by(BackupEntry.creation_time.desc()).\
            first()

        if last_db:
            last_backup = str(last_db.creation_time)[:19]
        else:
            last_backup = "none"

        session.close()

        print 'tableau-status: %s, main-state: %s, secondary-state: %s, last-backup: %s' % (tableau_status, main_state, secondary_state, last_backup)

        return {'tableau-status': tableau_status,
                'main-state': main_state,
                'secondary-state': secondary_state,
                'last-backup': last_backup
                }

class StatusDialog(DialogPage):

    NAME = "status"
    TEMPLATE = "status.mako"

    def __init__(self, global_conf):
        super(StatusDialog, self).__init__(global_conf)
        self.Session = sessionmaker(bind=meta.engine)

        domainname = store.get('palette', 'domainname')
        self.domain = Domain.get_by_name(domainname, Session=self.Session)

        session = self.Session()
        self.status_entries = session.query(StatusEntry).\
            join(AgentStatusEntry).\
            filter(AgentStatusEntry.domainid == self.domain.domainid).\
            all()

        # Dig out the main status and time
        self.main_status = "Unknown"
        self.status_time = "Unknown"
        for entry in self.status_entries:
            if entry.name == 'Status':
                self.main_status = entry.status
                self.status_time = str(entry.creation_time)[:19] # Cut off fraction
        session.close()
