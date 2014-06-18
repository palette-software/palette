import sqlalchemy
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, func
from sqlalchemy.orm.exc import NoResultFound
from webob import exc
import sys

from akiri.framework.config import store

from akiri.framework.ext.sqlalchemy import meta

from controller.tableau import TableauProcess
from controller.state import StateManager
from controller.agent import Agent
from controller.agentmanager import AgentManager
from controller.agentinfo import AgentVolumesEntry
from controller.domain import Domain
from controller.state_control import StateControl
from controller.util import sizestr, DATEFMT
from controller.system import LicenseEntry

from page import PalettePage
from event import EventApplication
from rest import PaletteRESTHandler

__all__ = ["MonitorApplication"]

class Colors(object):
    RED_NUM=1
    YELLOW_NUM=2
    GREEN_NUM=3

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

class MonitorApplication(PaletteRESTHandler):

    NAME = 'monitor'

    def __init__(self, global_conf):
        super(MonitorApplication, self).__init__(global_conf)
        self.event = EventApplication(global_conf)

    def disk_watermark(self, name):
        """ Threshold for the disk indicator. (low|high) """
        try:
            v = self.system.get('disk-watermark-'+name)
        except ValueError:
            return 100
        return int(v)

    def disk_color(self, used, size, low, high):
        if used > high * size:
            return 'red'
        if used > low * size:
            return 'yellow'
        return 'green'

    def volume_info(self, agentid):
        (low,high) = self.disk_watermark('low'), self.disk_watermark('high')

        volumes = []
        L = meta.Session.query(AgentVolumesEntry).\
            filter(AgentVolumesEntry.agentid == agentid).\
            order_by(AgentVolumesEntry.name).\
            all()
        for v in L:
            if not v.size or v.available_space is None:
                continue
            used = v.size - v.available_space
            value = '%s used of %s' % (sizestr(used), sizestr(v.size))
            color = self.disk_color(used, v.size, low, high)
            volumes.append({'name': v.name, 'value': value, 'color': color})
        return volumes

    def firewall_info(self, agentid):
        ports = [{'name':'HTTP', 'num':80, 'color':'green'},
                 {'name':'HTTPS', 'num':443, 'color':'green'},
                 {'name':'Palette Agent', 'num':8889, 'color':'green'},
                 {'name':'MSSQL Server', 'num':1433, 'color':'green'}
                 ]
        return ports

    def license_info(self, agentid):
        entry = LicenseEntry.get_by_agentid(agentid)
        if entry is None:
            return {'value':'unknown', 'color':'yellow'}
        if entry.valid():
            return {'value':'valid', 'color':'green'}
        else:
            return {'value':'invalid', 'color':'red'}

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
        # Get the state
        main_state = StateManager.get_state_by_envid(self.environment.envid)

        state_control_entry = StateControl.get_state_control_entry(main_state)
        if not state_control_entry:
            print "UNKNOWN STATE!  State:", main_state
            # fixme: stop everything?  Log this somewhere?
            return

        # Convert the space-sparated string to a list, e.g.
        # "start stop reset" --> ["start", "stop", "reset"]
        allowable_actions = state_control_entry.allowable_actions.split(' ')

        text = state_control_entry.text

        if main_state == StateManager.STATE_STOPPED:
            warning = text
        else:
            warning = ""

        # The overall color starts at the state_control color.
        # It can get worse (e.g. green to yellow or red) , but not better
        # (e.g. red to yellow or green).
        color = state_control_entry.color
        if color in Colors.color_to_num:
            color_num = Colors.color_to_num[color]
        else:
            color_num = Colors.RED_NUM

        if main_state in (StateManager.STATE_STOPPED,
                StateManager.STATE_STARTED, StateManager.STATE_DEGRADED,
                StateManager.STATE_PENDING, StateManager.STATE_DISCONNECTED,
                                                    StateManager.STATE_UNKNOWN):
            user_action_in_progress = False
        else:
            user_action_in_progress = True

        agent_entries = meta.Session.query(Agent).\
            filter(Agent.envid == self.environment.envid).\
            order_by(Agent.display_order).\
            all()

        agents = []
        for entry in agent_entries:
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

            agent['creation-time'] = entry.creation_time.strftime(DATEFMT)
            agent['modification_time'] = \
                entry.modification_time.strftime(DATEFMT)
            agent['last-connnection-time'] = \
                entry.last_connection_time.strftime(DATEFMT)
            agent['last-disconnect-time'] = \
                entry.last_disconnect_time.strftime(DATEFMT)

            if entry.agent_type == AgentManager.AGENT_TYPE_PRIMARY \
                    and entry.connected():
                primary = entry
                agent['license'] = self.license_info(entry.agentid)

            if entry.connected():
                if entry.agent_type == AgentManager.AGENT_TYPE_PRIMARY:
                    agent['license'] = self.license_info(entry.agentid)

                    lic_color = Colors.color_to_num[agent['license']['color']]
                    if lic_color < agent_color_num:
                        agent_color_num = lic_color

                agent['volumes'] = self.volume_info(entry.agentid)
                agent['ports'] = self.firewall_info(entry.agentid)

                vol_lowest_color = self.lowest_color(agent['volumes'])
                firewall_lowest_color = self.lowest_color(agent['ports'])

                if vol_lowest_color < agent_color_num:
                    agent_color_num = vol_lowest_color
                if firewall_lowest_color < agent_color_num:
                    agent_color_num = firewall_lowest_color
            else:
                agent_color_num = Colors.RED_NUM
                msg = 'Disconnected ' + agent['last-disconnect-time']
                agent['warnings'] = [{'color':'red', 'message': msg}]

            if entry.agent_type == AgentManager.AGENT_TYPE_PRIMARY and \
                                    main_state == StateManager.STATE_STOPPED:
                agent_color_num = Colors.RED_NUM
                agent['warnings'] = [{'color':'red',
                                      'message': 'Agent stopped'}]

            # Override: Tableau stopped --> primary agent is red
            if main_state == StateManager.STATE_STOPPED and \
                        entry.agent_type == AgentManager.AGENT_TYPE_PRIMARY:
                agent_color_num = Colors.RED_NUM

            if entry.agent_type == AgentManager.AGENT_TYPE_PRIMARY or \
                        entry.agent_type == AgentManager.AGENT_TYPE_WORKER:

                # Add tableau processes for this agent
                status_entries = meta.Session.query(TableauProcess).\
                    filter(TableauProcess.agentid == entry.agentid).\
                    order_by(TableauProcess.name).\
                    all()

                tableau_procs = []
                for entry in status_entries:
                    proc = {}

                    if entry.pid == 0:
                        continue

                    proc['pid'] = entry.pid
                    proc['name'] = entry.name
                    proc['status'] = entry.status
                    if entry.status == 'running':
                        proc['color'] = 'green'
                    else:
                        proc['color'] = 'red'
                        # The agent needs to be red too.
                        agent_color_num = Colors.RED_NUM

                    tableau_procs.append(proc)

                agent['details'] = tableau_procs
            else:
                # For now, only primaries and workers have details
                agent['details'] = []

            agent['color'] = Colors.color_to_str[agent_color_num]
            agents.append(agent)

            # Set the overall status lower if this agent status was lower.
            if agent_color_num < color_num:
                color_num = agent_color_num

        environments = [ { "name": "My Servers", "agents": agents } ]

        monitor_ret = {'state': main_state,
                       'allowable-actions': allowable_actions,
                       'text': text,
                       'color': Colors.color_to_str[color_num],
                       'user-action-in-progress': user_action_in_progress,
                       'environments': environments
                      }

        if warning:
            monitor_ret['warning'] = warning

        if not 'event' in req.GET or \
                    ('event' in req.GET and req.GET['event'] != 'false'):
            events = self.event.handle_get(req)
            monitor_ret['events'] = events['events']

        return monitor_ret

    def handle(self, req):
        if req.environ['PATH_INFO'] == '/monitor':
            return self.handle_monitor(req)
        raise exc.HTTPBadRequest()

class ConfigureMonitor(PalettePage):

    TEMPLATE = "configure_monitor.mako"
    def handle(self, req):
        return None

def make_configure_monitor(global_conf):
    return ConfigureMonitor(global_conf)
