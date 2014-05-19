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
from controller.state import StateManager
from controller.agentstatus import AgentStatusEntry
from controller.agentmanager import AgentManager
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
        # Get the state
        main_state = StateManager.get_state_by_domainid(self.domain.domainid)

        custom_state_entry = CustomStates.get_custom_state_entry(main_state)
        if not custom_state_entry:
            print "UNKNOWN STATE!  State:", main_state
            # fixme: stop everything?  Log this somewhere?
            return

        # Convert the space-sparated string to a list, e.g.
        # "start stop reset" --> ["start", "stop", "reset"]
        allowable_actions = custom_state_entry.allowable_actions.split(' ')

        text = custom_state_entry.text
        color = custom_state_entry.color

        if main_state in (StateManager.STATE_STOPPED,
                StateManager.STATE_STARTED, StateManager.STATE_DEGRADED,
                StateManager.STATE_PENDING, StateManager.STATE_DISCONNECTED,
                                                    StateManager.STATE_UNKNOWN):
            user_action_in_progress = False
        else:
            user_action_in_progress = True

        agent_entries = Session.query(AgentStatusEntry).\
            filter(AgentStatusEntry.domainid == self.domain.domainid).\
            order_by(AgentStatusEntry.display_order).\
            all()

        primary = None
        agents = []
        for entry in agent_entries:
            agent = {}
            agent['uuid'] = entry.uuid
            agent['displayname'] = entry.displayname
            agent['display_order'] = entry.display_order
            agent['hostname'] = entry.hostname
            agent['agent_type'] = entry.agent_type
            agent['version'] = entry.version
            agent['ip_address'] = entry.ip_address
            agent['listen_port'] = entry.listen_port
            agent['creation_time'] = str(entry.creation_time)[:19]
            agent['modification_time'] = str(entry.modification_time)[:19]
            agent['last_connnection_time'] = \
                                    str(entry.last_connection_time)[:19]
            agent['last_disconnect_time'] = str(entry.last_disconnect_time)[:19]
            if entry.agent_type == AgentManager.AGENT_TYPE_PRIMARY and \
                                                            entry.connected():
                primary = entry
                agent['color'] = color
            else:
                if entry.connected():
                    agent['color'] = 'green'
                else:
                    agent['color'] = 'red'

            if entry.agent_type == AgentManager.AGENT_TYPE_PRIMARY or \
                        entry.agent_type == AgentManager.AGENT_TYPE_WORKER:

                # Add tableau processes for this agent
                status_entries = Session.query(StatusEntry).\
                    filter(StatusEntry.agentid == entry.agentid).\
                    order_by(StatusEntry.name).\
                    all()

                tableau_procs = []
                for entry in status_entries:
                    proc = {}

                    proc['pid'] = entry.pid
                    proc['name'] = entry.name
                    proc['creation_time']  = str(entry.creation_time)[:19]
                    proc['modification_time'] = \
                                            str(entry.modification_time)[:19]
                    tableau_procs.append(proc)

                agent['details'] = tableau_procs
            else:
                # For now, only primaries and workers have details
                agent['details'] = []

            agents.append(agent)

        environments = [ { "name": "My Servers", "agents": agents } ]

        return {'state': main_state,
                'allowable-actions': allowable_actions,
                'text': text,
                'color': color,
                'user-action-in-progress': user_action_in_progress,
                'environments': environments
               }

    def handle(self, req):
        if req.environ['PATH_INFO'] == '/monitor':
            return self.handle_monitor(req)
        raise exc.HTTPBadRequest()

class ConfigureMonitor(UserInterfaceRenderer):

    TEMPLATE = "configure_monitor.mako"
    def handle(self, req):
        return None

def make_configure_monitor(global_conf):
    return ConfigureMonitor(global_conf)
