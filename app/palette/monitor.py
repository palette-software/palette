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
from controller.firewall_manager import FirewallEntry, FirewallManager
from controller.profile import UserProfile, Role
from controller.state_control import StateControl
from controller.util import sizestr, DATEFMT
from controller.system import LicenseEntry
from controller.sites import Site
from controller.projects import Project
from controller.extracts import ExtractManager
from controller.event_control import EventControl

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

    def getindex(self, req, name):
        try:
            return int(req.GET[name])
        except:
            pass
        return 0

    def status_options(self, req):
        c = 'status' in req.GET and req.GET['status'] or '0'
        L = [{'item':'All Status', 'id':0}] + \
            [{'item':EventControl.level_strings[x], 'id':x} \
                 for x in EventControl.level_strings]
        value = (c == '0') and L[0]['item'] or EventControl.level_strings[c]
        return {'name':'status', 'value':value, 'id':c, 'options':L}

    def type_options(self, req):
        c = 'type' in req.GET and req.GET['type'] or '0'
        L = [{'item':'All Types', 'id':0}]

        d = {'name':'type'}
        for t in EventControl.types():
            if t == c:
                d['value'] = d['id'] = t
            L.append({'item':t, 'id':t})
        if 'id' not in d:
            d['value'] = L[0]['item']
            d['id'] = 0
        d['options'] = L
        return d
    
    def site_options(self, req):
        index = self.getindex(req, 'site')
        L = [{'item':'All Sites', 'id':0}] + \
            [{'item':x.name, 'id':x.siteid} for x in Site.all()]
        if index >= len(L):
            index = 0
        return {'name':'site',
                'value':L[index]['item'], 'id':L[index]['id'], 
                'options':L}

    def project_options(self, req):
        index = self.getindex(req, 'project')
        L = [{'item':'All Projects', 'id':0}] + \
            [{'item':x.name, 'id':x.projectid} for x in Project.all()]
        if index >= len(L):
            index = 0
        return {'name':'project',
                'value':L[index]['item'], 'id':L[index]['id'], 
                'options':L}

    def publisher_options(self, req):
        sysid = self.getindex(req, 'publisher')
        publishers = ExtractManager.publishers()
        L = [{'item':'All Publishers', 'id':0}]
        d = {'name':'publisher'}
        for p in ExtractManager.publishers():
            if p.system_users_id == sysid:
                d['value'] = p.friendly_name
                d['id'] = p.system_users_id
            L.append({'item':p.friendly_name, 'id':p.system_users_id})
        if not 'id' in d:
            d['value'] = L[0]['item']
            d['id'] = L[0]['id']
        d['options'] = L
        return d

    def disk_watermark(self, name):
        """ Threshold for the disk indicator. (low|high) """
        try:
            v = self.system.get('disk-watermark-'+name)
        except ValueError:
            return float(100)
        return float(v)

    def disk_color(self, used, size, low, high):
        if used > high / 100 * size:
            return 'red'
        if used > low / 100 * size:
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
        ports = []

        rows = meta.Session.query(FirewallEntry).\
            filter(FirewallEntry.agentid == agentid).\
            all()

        for entry in rows:
            fw_dict = {'name': entry.name,
                        'num': entry.port,
                        'color': entry.color
            }
            ports.append(fw_dict)

        ports = sorted(ports, key=lambda port: port['num'])
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

        # FIXME: hack
        if isinstance(req.remote_user, basestring):
            req.remote_user = UserProfile.get_by_name(req.remote_user)

        allowable_actions = []
        if req.remote_user.roleid >= Role.MANAGER_ADMIN:
            # Convert the space-sparated string to a list, e.g.
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
            if entry.last_disconnect_time:
                agent['last-disconnect-time'] = \
                    entry.last_disconnect_time.strftime(DATEFMT)

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
                msg = 'Disconnected'
                if 'last-disconnect-time' in agent:
                    msg = msg + ' ' + agent['last-disconnect-time']
                agent['warnings'] = [{'color':'red', 'message': msg}]

            if entry.agent_type == AgentManager.AGENT_TYPE_PRIMARY and \
                                    main_state == StateManager.STATE_STOPPED:
                agent_color_num = Colors.RED_NUM
                agent['warnings'] = [{'color':'red',
                                      'message': 'Tableau stopped'}]

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

        config = [self.status_options(req),
                  self.type_options(req),
                  self.site_options(req),
                  self.publisher_options(req),
                  self.project_options(req)]

        monitor_ret = {'state': main_state,
                       'allowable-actions': allowable_actions,
                       'text': state_control_entry.text,
                       'icon': state_control_entry.icon,
                       'color': Colors.color_to_str[color_num],
                       'user-action-in-progress': user_action_in_progress,
                       'environments': environments,
                       'config': config
                      }

        if not 'event' in req.GET or \
                    ('event' in req.GET and req.GET['event'] != 'false'):
            event_status = "0"
            event_type = "0"
            event_site = 0
            event_publisher = 0
            event_project = 0

            if 'status' in req.GET:
                event_status = req.GET['status']
            if 'type' in req.GET:
                event_type = req.GET['type']
            if 'site' in req.GET:
                if req.GET['site'].isdigit():
                    event_site = int(req.GET['site'])
                else:
                    print "Invalid event site:", req.GET['site']

            if 'publisher' in req.GET:
                if req.GET['publisher'].isdigit():
                    event_publisher = int(req.GET['publisher'])
                else:
                    print "Invalid event publisher:", req.GET['publisher']

            if req.remote_user.roleid == Role.NO_ADMIN:
                event_publisher = req.remote_user.system_users_id

            if 'project' in req.GET:
                if req.GET['project'].isdigit():
                    event_project = int(req.GET['project'])
                else:
                    print "Invalid event project:", req.GET['project']

            events = self.event.handle_get(req,
                event_status=event_status,
                event_type=event_type,
                event_site=event_site,
                event_publisher=event_publisher,
                event_project=event_project)

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
