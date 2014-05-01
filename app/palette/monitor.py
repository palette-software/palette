import sqlalchemy
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, func
from sqlalchemy.orm.exc import NoResultFound
import sys

from akiri.framework.api import RESTApplication, DialogPage, UserInterfaceRenderer
from akiri.framework.config import store

from controller.meta import Session
from controller.status import StatusEntry
from controller.state import StateEntry, StateManager
from controller.backup import BackupEntry
from controller.agentstatus import AgentStatusEntry
from controller.domain import Domain
from controller.custom_states import CustomStates

__all__ = ["MonitorApplication"]

class MonitorApplication(RESTApplication):

    NAME = 'monitor'

    def __init__(self, global_conf):
        super(MonitorApplication, self).__init__(global_conf)

        domainname = store.get('palette', 'domainname')
        self.domain = Domain.get_by_name(domainname)


    def handle(self, req):

        try:
            primary_agents = Session.query(AgentStatusEntry).\
                filter(AgentStatusEntry.domainid == self.domain.domainid).\
                filter(AgentStatusEntry.agent_type == "primary").\
                all()
        except NoResultFound, e:
            primary_agents = None

        # If there is more than one primary agent in the table, look for
        # the primary agent that is connected and use that.
        # the table.

        primary = None

        # Set defaults
        tableau_status = "unknown"
        main_state = StateEntry.STATE_UNKNOWN
        text = "none"
        color = "none"
        user_action_in_progress = False

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
        # main, and backup states.
        if primary:
            # Dig out the tableau status.
            try:
                tableau_entry = Session.query(StatusEntry).\
                    join(AgentStatusEntry).\
                    filter(AgentStatusEntry.domainid == self.domain.domainid).\
                    filter(StatusEntry.name == 'Status').\
                    one()
                tableau_status = tableau_entry.status
            except NoResultFound, e:
                pass

            # Dig out the last/most recent backup.
            last_db = Session.query(BackupEntry).\
                join(AgentStatusEntry).\
                filter(AgentStatusEntry.domainid == self.domain.domainid).\
                filter(StatusEntry.name == 'Status').\
                order_by(BackupEntry.creation_time.desc()).\
                first()

            if last_db:
                last_backup = str(last_db.creation_time)[:19]
            else:
                last_backup = "none"
        else:
            last_backup = "unknown"

        # Get the state
        main_state = StateManager.get_state_by_domainid(self.domain.domainid)

        state_entry = CustomStates.get_custom_state_entry(main_state)
        if not state_entry:
            print "UNKNOWN STATE!  State:", main_state
            # fixme: stop everything?  Log this somewhere?
            return

        text = state_entry.text
        color = state_entry.color

        if main_state in (StateEntry.STATE_STOPPED,
                StateEntry.STATE_STARTED, StateEntry.STATE_DEGRADED,
                StateEntry.STATE_PENDING, StateEntry.STATE_DISCONNECTED,
                                                    StateEntry.STATE_UNKNOWN):
            user_action_in_progress = False
        else:
            user_action_in_progress = True

        return {'tableau-status': tableau_status,
                'state': main_state,
                'text': text,
                'color': color,
                'user-action-in-progress': user_action_in_progress,
                'last-backup': last_backup
               }

class StatusDialog(DialogPage):

    NAME = "status"
    TEMPLATE = "status.mako"

    def __init__(self, global_conf):
        super(StatusDialog, self).__init__(global_conf)

        domainname = store.get('palette', 'domainname')
        self.domain = Domain.get_by_name(domainname)

        self.status_entries = Session.query(StatusEntry).\
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

class ConfigureMonitor(UserInterfaceRenderer):

    TEMPLATE = "configure_monitor.mako"
    def handle(self, req):
        return None

def make_configure_monitor(global_conf):
    return ConfigureMonitor(global_conf)
