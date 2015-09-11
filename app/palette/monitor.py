from sqlalchemy import or_
from webob import exc
from collections import OrderedDict

import akiri.framework.sqlalchemy as meta

from controller.tableau import TableauProcess
from controller.state import StateManager
from controller.agent import Agent, AgentVolumesEntry
from controller.agentmanager import AgentManager
from controller.firewall_manager import FirewallEntry
from controller.ports import PortEntry
from controller.profile import Role
from controller.state_control import StateControl
from controller.util import sizestr, DATEFMT, utc2local
from controller.licensing import LicenseEntry
from controller.event_control import EventControl
from controller.notifications import NotificationManager
from controller.system import SystemKeys

from .option import DictOption
from .event import EventHandler
from .rest import PaletteRESTApplication

__all__ = ["MonitorApplication"]

BUY_URL = 'https://licensing.palette-software.com/buy'

class Colors(object):
    RED_NUM = 1
    YELLOW_NUM = 2
    GREEN_NUM = 3

    color_to_str = {
        RED_NUM: "red",
        YELLOW_NUM: "yellow",
        GREEN_NUM: "green"
    }

    color_to_num = {
        'red': RED_NUM,
        'yellow': YELLOW_NUM,
        'green': GREEN_NUM
    }

class EventStatus(DictOption):
    """Representation for the Events status dropdown."""
    NAME = 'status-dropdown'
    ALL = 0
    ERROR = EventControl.LEVEL_ERROR
    WARNING = EventControl.LEVEL_WARNING
    INFO = EventControl.LEVEL_INFO

    def __init__(self, valueid):
        options = OrderedDict({})
        options[self.ALL] = 'All Status'
        for level in [self.ERROR, self.WARNING, self.INFO]:
            options[level] = EventControl.level_strings[level]
        super(EventStatus, self).__init__(self.NAME, valueid, options)


class EventType(DictOption):
    """Representation for the Events type dropdown."""
    NAME = 'type-dropdown'
    ALL = 0

    def __init__(self, valueid):
        type_list = sorted(EventControl.all_types.items(),
                           key=lambda item: item[1])
        options = OrderedDict([(self.ALL, 'All Types')] + type_list)
        super(EventType, self).__init__(self.NAME, valueid, options)

def known_agents(envid):
    """Return all the known agents for the specified environment."""
    query = meta.query(Agent).filter(Agent.envid == envid).\
            order_by(Agent.display_order).order_by(Agent.displayname)
    return query.all()

# agents is the sqlalchemy objects
def calculate_main_state(req, agents):
    """Determine the main state of the environment from the agents connected.
    This is the overall state as shown to administrators (not publishers)
    """
    if req.system[SystemKeys.UPGRADING]:
        return StateManager.STATE_UPGRADING

    for entry in agents:
        if entry.agent_type == AgentManager.AGENT_TYPE_PRIMARY:
            if not entry.enabled:
                return StateManager.STATE_PRIMARY_NOT_ENABLED
            else:
                # one primary per environment so no need to continue
                break

    main_state = req.system[SystemKeys.STATE]
    if main_state is None:
        return StateManager.STATE_DISCONNECTED
    return main_state


class MonitorApplication(PaletteRESTApplication):
    """The main monitor callback to handle status and event updates."""
    def __init__(self):
        super(MonitorApplication, self).__init__()
        self.event = EventHandler()

    def status_options(self, req):
        valueid = req.params_get('status', '0')
        if valueid == '0':
            valueid = EventStatus.ALL
        return EventStatus(valueid).default()

    def type_options(self, req):
        valueid = req.params_get('type', '0')
        if valueid == '0':
            valueid = EventType.ALL
        return EventType(valueid).default()

    # FIXME - remove and/or use SystemKeys
    def disk_watermark(self, req, name):
        """ Threshold for the disk indicator. (low|high) """
        try:
            value = req.system['disk-watermark-'+name]
        except ValueError:
            return float(100)
        return float(value)

    def disk_color(self, used, size, low, high):
        if used > high / 100 * size:
            return 'red'
        if used > low / 100 * size:
            return 'yellow'
        return 'green'

    def volume_info(self, req, agent):
        low = self.disk_watermark(req, 'low')
        high = self.disk_watermark(req, 'high')

        volumes = []
        query = meta.Session.query(AgentVolumesEntry).\
            filter(AgentVolumesEntry.agentid == agent.agentid)
        if agent.iswin:
            query = query.filter(or_(AgentVolumesEntry.vol_type == 'Fixed',
                             AgentVolumesEntry.vol_type == 'Network'))
        for vol in query.order_by(AgentVolumesEntry.name).all():
            if not vol.size or vol.available_space is None:
                continue
            used = vol.size - vol.available_space
            value = '%s free of %s' % \
                (sizestr(vol.available_space), sizestr(vol.size))
            color = self.disk_color(used, vol.size, low, high)
            volumes.append({'name': vol.name, 'value': value, 'color': color})
        return volumes

    def firewall_info(self, agent):
        rows = meta.Session.query(FirewallEntry).\
            filter(FirewallEntry.agentid == agent.agentid).\
            order_by(FirewallEntry.port).\
            all()

        ports = []
        for entry in rows:
            fw_dict = {'name': entry.name,
                        'num': entry.port,
                        'color': entry.color
            }
            ports.append(fw_dict)

        return ports

    def out_ports(self, agent):

        rows = meta.Session.query(PortEntry).\
            filter(PortEntry.agentid == agent.agentid).\
            filter(PortEntry.color != None).\
            order_by(PortEntry.dest_port).\
            all()

        ports = []
        for entry in rows:
            out_dict = {'name': entry.service_name,
                        'num': entry.dest_port,
                        'color': entry.color}
            ports.append(out_dict)

        return ports

    def license_info(self, agentid):
        entry = LicenseEntry.get_by_agentid(agentid)
        if entry is None:
            return {'value':'unknown', 'color':'green'}
        if entry.valid():
            return {'value':'valid', 'color':'green'}
        else:
            return {'value':'invalid', 'color':'red'}

    def cpu_info(self, envid, agent_entry):
        cpu_entry = NotificationManager.get_entry_by_envid_name_agentid(
                    envid, 'cpu', agent_entry.agentid)
        if cpu_entry and cpu_entry.color:
            return {'color': cpu_entry.color}

        # Report green unless proven otherwise.
        return {'color': 'green'}

    def lowest_color(self, info_list):
        lowest_color_num = Colors.GREEN_NUM

        for info in info_list:
            if not 'color' in info:
                continue
            color_num = Colors.color_to_num[info['color']]
            if color_num < lowest_color_num:
                lowest_color_num = color_num

        return lowest_color_num

    def handle_monitor(self, req):
        """Collect all state for this environment needed by the UI."""

        # FIXME: just generate a list of dicts here using agent.todict()
        agent_entries = known_agents(req.envid)

        main_state = calculate_main_state(req, agent_entries)

        state_control_entry = StateControl.get_state_control_entry(main_state)
        if not state_control_entry:
            print "UNKNOWN STATE!  State:", main_state
            # fixme: stop everything?  Log this somewhere?
            return

        if req.remote_user.roleid == Role.NO_ADMIN:
            # publisher:
            monitor_ret = self.get_publisher_view(main_state)
        else:
            monitor_ret = self.get_admin_view(req, main_state,
                                              state_control_entry,
                                              agent_entries)

        config = [self.status_options(req), self.type_options(req)]
        monitor_ret['config'] = config

        seq = req.params_getint('seq')
        if not seq is None:
            monitor_ret['seq'] = seq

        if not 'event' in req.GET or \
           ('event' in req.GET and req.GET['event'] != 'false'):

            events = self.event.handle_GET(req)
            monitor_ret['events'] = events['events']
            monitor_ret['item-count'] = events['count']

        monitor_ret['interval'] = 1000 # ms

        return monitor_ret

    def get_admin_view(self, req, main_state, state_control_entry,
                       agent_entries):
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        """Return information for an administrator."""
        allowable_actions = []
        if req.remote_user.roleid >= Role.MANAGER_ADMIN:
            # Convert the space-separated string to a list, e.g.
            # "start stop reset" --> ["start", "stop", "reset"]
            s = state_control_entry.allowable_actions
            if s:
                allowable_actions = s.split(' ')

        # The overall color starts at the state_control color.
        # It can get worse (e.g. green to yellow or red) , but not better
        # (e.g. red to yellow or green).
        color = state_control_entry.color
        if color in Colors.color_to_num:
            color_num = Colors.color_to_num[color]
        else:
            color_num = Colors.RED_NUM

        if main_state in (StateManager.STATE_STOPPED,
                StateManager.STATE_STOPPED_UNEXPECTED,
                StateManager.STATE_STARTED, StateManager.STATE_DEGRADED,
                StateManager.STATE_PENDING, StateManager.STATE_DISCONNECTED):
            user_action_in_progress = False
        else:
            user_action_in_progress = True

        agent_worker_problem = False
        agents = []
        for entry in agent_entries:
            if not entry.enabled:
                continue
            # Start out green until proven otherwise
            agent_color_num = Colors.GREEN_NUM

            agent = {}
            agent['uuid'] = entry.uuid
            agent['displayname'] = entry.displayname
            agent['display_order'] = entry.display_order
            agent['hostname'] = entry.hostname
            agent['agent_type'] = entry.agent_type
            agent['version'] = entry.version
            agent['ip_address'] = entry.ip_address
            agent['listen_port'] = entry.listen_port

            if entry.creation_time:
                # Since creation_time is set on commit() there is a very
                # small window where the creation_time may be None.
                creation_time = utc2local(entry.creation_time)
                agent['creation-time'] = creation_time.strftime(DATEFMT)
            if entry.modification_time != None:
                modtime = utc2local(entry.modification_time)
                agent['modification_time'] = modtime.strftime(DATEFMT)
            else:
                agent['modification_time'] = ""

            last_connection_time = utc2local(entry.last_connection_time)
            agent['last-connnection-time'] = \
                                    last_connection_time.strftime(DATEFMT)
            if entry.last_disconnect_time:
                last_disconnect_time = utc2local(entry.last_disconnect_time)
                agent['last-disconnect-time'] = \
                                    last_disconnect_time.strftime(DATEFMT)

            if main_state in (StateManager.STATE_DISCONNECTED,
                              StateManager.STATE_PENDING) and \
                          entry.agent_type == AgentManager.AGENT_TYPE_PRIMARY:
                agent_color_num = Colors.RED_NUM
                if main_state == StateManager.STATE_DISCONNECTED:
                    # "Tableau Status Unknown"
                    msg = 'Disconnected'
                    if 'last-disconnect-time' in agent:
                        msg = msg + ' ' + agent['last-disconnect-time']
                elif main_state == StateManager.STATE_PENDING:
                    # "Retrieving Tableau Status"
                    msg = "Retrieving Tableau Status"
                else:
                    # UNKNOWN: An agent has never connected
                    msg = 'No agent has ever connected'
                agent['warnings'] = [{'color':'red', 'message': msg}]
            elif entry.connected():
                if entry.agent_type == AgentManager.AGENT_TYPE_PRIMARY:
                    agent['license'] = self.license_info(entry.agentid)

                    lic_color = Colors.color_to_num[agent['license']['color']]
                    if lic_color < agent_color_num:
                        agent_color_num = lic_color

                agent['volumes'] = self.volume_info(req, entry)
                agent['in_ports'] = self.firewall_info(entry)
                agent['out_ports'] = self.out_ports(entry)
                cpu_info = self.cpu_info(req.envid, entry)
                if cpu_info:
                    agent['cpu'] = cpu_info
                    cpu_color = Colors.color_to_num[cpu_info['color']]
                    if cpu_color < agent_color_num:
                        agent_color_num = cpu_color

                vol_lowest_color = self.lowest_color(agent['volumes'])
                firewall_lowest_color = self.lowest_color(agent['in_ports'])
                out_ports_lowest_color = self.lowest_color(agent['out_ports'])

                if vol_lowest_color < agent_color_num:
                    agent_color_num = vol_lowest_color
                if firewall_lowest_color < agent_color_num:
                    agent_color_num = firewall_lowest_color
                if out_ports_lowest_color < agent_color_num:
                    agent_color_num = out_ports_lowest_color
            else:
                agent_color_num = Colors.RED_NUM
                msg = 'Disconnected'
                if 'last-disconnect-time' in agent:
                    msg = msg + ' ' + agent['last-disconnect-time']
                agent['warnings'] = [{'color':'red', 'message': msg}]

            if entry.agent_type in (AgentManager.AGENT_TYPE_PRIMARY,
                                    AgentManager.AGENT_TYPE_WORKER) and \
                                    main_state == StateManager.STATE_STOPPED:
                agent_color_num = Colors.YELLOW_NUM
                agent['warnings'] = [{'color':'yellow',
                                      'message': 'Tableau stopped'}]
                if entry.agent_type == AgentManager.AGENT_TYPE_WORKER:
                    agent_worker_problem = True
            elif entry.agent_type in (AgentManager.AGENT_TYPE_PRIMARY,
                                    AgentManager.AGENT_TYPE_WORKER) and \
                        main_state == StateManager.STATE_STOPPED_UNEXPECTED:
                agent_color_num = Colors.RED_NUM
                agent['warnings'] = [{'color':'red',
                                      'message': 'Tableau stopped'}]
                if entry.agent_type == AgentManager.AGENT_TYPE_WORKER:
                    agent_worker_problem = True

            if entry.agent_type == AgentManager.AGENT_TYPE_PRIMARY or \
                        entry.agent_type == AgentManager.AGENT_TYPE_WORKER:

                # Add tableau processes for this agent
                status_entries = meta.Session.query(TableauProcess).\
                    filter(TableauProcess.agentid == entry.agentid).\
                    order_by(TableauProcess.name).\
                    all()

                tableau_procs = []
                for tab_entry in status_entries:
                    proc = {}

                    if tab_entry.pid == 0:
                        continue

                    if tab_entry.pid == -1:
                        # Special case: Error such as
                        # ""Connection error contacting worker 1"
                        agent_color_num = Colors.RED_NUM
                        agent['warnings'] = [{'color':'red',
                                              'message': tab_entry.name}]
                        # This in the main state being set to DEGRADED.
                        agent_worker_problem = True
                        continue

                    if tab_entry.pid > 0:
                        proc['pid'] = tab_entry.pid
                    else:
                        proc['pid'] = tab_entry.status

                    proc['name'] = tab_entry.name
                    proc['status'] = tab_entry.status
                    # 'tabadminstatus -v' reports processes status with
                    # ".... is running".
                    # systeminfo reports Active, Passive, etc.
                    if tab_entry.status.find('running') != -1 or \
                        tab_entry.status in ('Active', 'Passive', 'Busy',
                                             'ReadOnly', 'ActiveSyncing'):
                        proc['color'] = 'green'
                    else:
                        # Includes "Unlicensed" which should also be red.
                        proc['color'] = 'red'
                        # The agent needs to be red too.
                        agent_color_num = Colors.RED_NUM

                    tableau_procs.append(proc)

                agent['details'] = tableau_procs

                if entry.agent_type == AgentManager.AGENT_TYPE_WORKER and \
                                                    not len(status_entries):
                    # If a worker doesn't have any Tableau processes listed,
                    # then make the worker RED with a message.
                    # This is probably due to the primary not being
                    # connected or not receiving tableau status yet.
                    warning = {'color': 'red',
                               'message': 'Tableau processes unavailable'}

                    if 'warnings' in agent:
                        agent['warnings'].append(warning)
                    else:
                        agent['warnings'] = warning

                    agent_color_num = Colors.RED_NUM
                    # This in the main state being set to DEGRADED.
                    agent_worker_problem = True

            else:
                # For now, only primaries and workers have details
                agent['details'] = []

            agent['color'] = Colors.color_to_str[agent_color_num]
            agents.append(agent)

            # Set the overall status lower if this agent status was lower.
            if agent_color_num < color_num:
                color_num = agent_color_num

        # If the primary is running and any worker has a problem, set
        # the status to DEGRADED.
        if main_state == StateManager.STATE_STARTED and agent_worker_problem:
            main_state = StateManager.STATE_DEGRADED
            # allowable_actions are the same for STARTED and DEGRADED, so
            # we don't need to update.
            state_control_entry = \
                            StateControl.get_state_control_entry(main_state)
            if not state_control_entry:
                print "UNKNOWN STATE.  State:", main_state
                # fixme: stop everything?  Log this somewhere?
                return

            color_num = Colors.RED_NUM

        # Special case: If Upgrading, set the main state to
        # "upgrading", etc.
        if main_state == StateManager.STATE_UPGRADING:
            state_control_entry = \
                            StateControl.get_state_control_entry(main_state)
            if not state_control_entry:
                print "UNKNOWN STATE!  State:", main_state
                # fixme: stop everything?  Log this somewhere?
                return

            allowable_actions = []
            if req.remote_user.roleid >= Role.MANAGER_ADMIN:
                # Convert the space-separated string to a list, e.g.
                # "start stop reset" --> ["start", "stop", "reset"]
                s = state_control_entry.allowable_actions
                if s:
                    allowable_actions = s.split(' ')

            color = state_control_entry.color
            if color in Colors.color_to_num:
                color_num = Colors.color_to_num[color]
            else:
                color_num = Colors.RED_NUM

        trial_days = req.palette_domain.trial_days()
        license_key = req.palette_domain.license_key
        if license_key is None:
            license_key = '' # development only
        buy_url = BUY_URL + '?key=' + license_key

        environments = [{"name": "My Machines", "agents": agents}]

        data = {'state': main_state,
                'allowable-actions': allowable_actions,
                'text': state_control_entry.text,
                'icon': state_control_entry.icon,
                'color': Colors.color_to_str[color_num],
                'user-action-in-progress': user_action_in_progress,
                'environments': environments,
                'admin': True,
                'license-key': req.palette_domain.license_key
                }

        if not trial_days is None:
            data['trial-days'] = trial_days
            data['buy-url'] = buy_url
        return data

    def get_publisher_view(self, main_state):
        """Return information for a publisher."""

        if main_state in (StateManager.STATE_PENDING,
                          StateManager.STATE_DISCONNECTED):
            # Set to report "...Unknown..."
            main_state = StateManager.STATE_DISCONNECTED
        elif main_state == StateManager.STATE_DEGRADED:
            # it is already set to degraded
            pass
        elif main_state.find('STARTED') != -1:
            # Anything that is started is reduced to "STARTED"
            main_state = StateManager.STATE_STARTED
        else:
            # All other states are a version of STOPPED
            main_state = StateManager.STATE_STOPPED

        state_control_entry = StateControl.get_state_control_entry(main_state)
        if not state_control_entry:
            print "UNKNOWN STATE!  State:", main_state
            # fixme: stop everything?  Log this somewhere?
            return

        color = state_control_entry.color
        if color in Colors.color_to_num:
            color_num = Colors.color_to_num[color]
        else:
            color_num = Colors.RED_NUM

        return {'state': main_state,
                'text': state_control_entry.text,
                'icon': state_control_entry.icon,
                'color': Colors.color_to_str[color_num],
                'admin': False
               }

    def service(self, req):
        if req.method != 'GET':
            raise exc.HTTPMethodNotAllowed()
        return self.handle_monitor(req)
