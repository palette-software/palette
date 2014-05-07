import sqlalchemy
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, func
from sqlalchemy.orm.exc import NoResultFound
from webob import exc
import sys

from akiri.framework.api import RESTApplication, DialogPage, UserInterfaceRenderer
from akiri.framework.config import store

from controller.meta import Session
from controller.status import StatusEntry
from controller.state import StateEntry, StateManager
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

    def handle_monitor(self, eq):
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

        # If there is a primary agent connected, get tableau status and
        # main state, etc.
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

        # Get the state
        main_state = StateManager.get_state_by_domainid(self.domain.domainid)

        try:
            state_entry = Session.query(StateEntry).\
                filter(StateEntry.domainid == self.domain.domainid).\
                one()
        except NoResultFound, e:
            main_state = StateEntry.STATE_DISCONNECTED
            allowable_actions_str = ""
        else:
            main_state = state_entry.state
            allowable_actions_str = state_entry.allowable_actions
            if allowable_actions_str == None:
                allowable_actions_str = ""

        # Convert the space-sparated string to a list, e.g.
        # "start stop reset" --> ["start", "stop", "reset"]
        allowable_actions = allowable_actions_str.split(' ')

        custom_state_entry = CustomStates.get_custom_state_entry(main_state)
        if not custom_state_entry:
            print "UNKNOWN STATE!  State:", main_state
            # fixme: stop everything?  Log this somewhere?
            return

        text = custom_state_entry.text
        color = custom_state_entry.color

        if main_state in (StateEntry.STATE_STOPPED,
                StateEntry.STATE_STARTED, StateEntry.STATE_DEGRADED,
                StateEntry.STATE_PENDING, StateEntry.STATE_DISCONNECTED,
                                                    StateEntry.STATE_UNKNOWN):
            user_action_in_progress = False
        else:
            user_action_in_progress = True

        data = {}

        agent_entries = Session.query(AgentStatusEntry).\
            filter(AgentStatusEntry.domainid == self.domain.domainid).\
            all()

        production_agents = []
        for entry in agent_entries:
            agent = {}
            agent['uuid'] = entry.uuid
            agent['displayname'] = entry.displayname
            agent['hostname'] = entry.hostname
            agent['agent_type'] = entry.agent_type
            agent['version'] = entry.version
            agent['ip_address'] = entry.ip_address
            agent['listen_port'] = entry.listen_port
            agent['creation_time'] = str(entry.creation_time)[:19]
            agent['modification_time'] = str(entry.modification_time)[:19]
            agent['last_connnection_time'] = str(entry.last_connection_time)[:19]
            agent['last_disconnect_time'] = str(entry.last_disconnect_time)[:19]
            if entry.connected():
                agent['color'] = 'green'
            else:
                agent['color'] = 'red'
            production_agents.append(agent)

        environments = [ { "name": "Production",
                            "agents": production_agents} ]

        return {'tableau-status': tableau_status,
                'state': main_state,
                'allowable_actions': allowable_actions,
                'text': text,
                'color': color,
                'user-action-in-progress': user_action_in_progress,
                'environments': environments
               }

        return data

    def handle(self, req):
        if req.environ['PATH_INFO'] == '/monitor':
            return self.handle_monitor(req)
        raise exc.HTTPBadRequest()

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
