import logger
import string
import threading
import time
import os
import re
from urlparse import urlparse
import json
import httplib
import socket
import exc
import xml.etree.ElementTree as ET

from sqlalchemy import Column, Integer, BigInteger, String, DateTime, func
from sqlalchemy.schema import ForeignKey
from sqlalchemy.orm.exc import NoResultFound

from util import traceback_string

import akiri.framework.sqlalchemy as meta

from state import StateManager
from agentmanager import AgentManager
from agent import Agent
from event_control import EventControl
from state_transitions import TRANSITIONS
from general import SystemConfig
from util import  success
from yml import YmlEntry

class SysteminfoException(Exception):
    def __init__(self, errnum, message):
        super(SysteminfoException, self).__init__(message)
        self.errnum = errnum
        self.message = message

class SysteminfoError(object):
    CONNECT_FAILURE = 1
    COMM_FAILURE = 2    # communication failure
    COMM_TIMEDOUT = 3    # communication failure
    NOT_FOUND = 4
    UNEXPECTED_RESPONSE = 5
    PARSE_FAILURE = 6
    JSON_PARSE_FAILURE = 7

class TableauProcess(meta.Base):
    # pylint: disable=no-init
    # NOTE: the above warning is erroneous generated for this class.
    __tablename__ = 'tableau_processes'

    ### Possible status as reported by "tabadmin status [...]"
    STATUS_RUNNING = "RUNNING"
    STATUS_STOPPED = "STOPPED"
    STATUS_DEGRADED = "DEGRADED"
    STATUS_UNKNOWN = "UNKNOWN"    # We set this if we don't know yet.

    tid = Column(BigInteger, primary_key=True)
    name = Column(String, nullable=False)
    agentid = Column(BigInteger,
                     ForeignKey("agent.agentid", ondelete='CASCADE'),
                     nullable=False, primary_key=True)
    pid = Column(Integer)
    status = Column(String)
    creation_time = Column(DateTime, server_default=func.now())
    modification_time = Column(DateTime, server_default=func.now(),
                               server_onupdate=func.current_timestamp())

class TableauStatusMonitor(threading.Thread):
    # pylint: disable=too-many-instance-attributes

    # Note: If there is a value in the system table, it is
    # used instead of these defaults.
    # Default interval for checking tableau status (in seconds)
    STATUS_REQUEST_INTERVAL_DEFAULT = 30

    # Minimum amount of time that must elapse while DEGRADED
    # before sending out the DEGRADED event.
    EVENT_DEGRADED_MIN_DEFAULT = 120    # in seconds

    LOGGER_NAME = "status"

    # Possible return values when attempting to get systeminfo:
    # Only considered a failure if the http get of the URL
    # can't accept a connection.  Otherwise, Tableau could be up.
    SYSTEMINFO_SUCCESS = 1
    SYSTEMINFO_FAIL = 2

    # Remember the url that worked with systeminfo to help determine
    # if tableau is really stopped when systeminfo fails.
    systeminfo_url_worked = None

    statemap = {
        TableauProcess.STATUS_RUNNING: StateManager.STATE_STARTED,
        TableauProcess.STATUS_STOPPED: StateManager.STATE_STOPPED,
        TableauProcess.STATUS_DEGRADED: StateManager.STATE_DEGRADED,
        TableauProcess.STATUS_UNKNOWN: StateManager.STATE_DISCONNECTED
    }

    def __init__(self, server, manager):
        super(TableauStatusMonitor, self).__init__()
        self.server = server
        self.rwlock = self.server.upgrade_rwlock
        self.manager = manager # AgentManager instance
        self.st_config = SystemConfig(server.system)
        self.log = logger.get(self.LOGGER_NAME)
        self.log.setLevel(self.st_config.debug_level)
        self.envid = self.server.environment.envid

        self.first_degraded_time = None
        self.sent_degraded_event = False

        # Start fresh: status table
        session = meta.Session()
        self.remove_all_status()
        session.commit()

        self.stateman = StateManager(self.server)

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

    def _add(self, agentid, name, pid, status):
        """Note a session is passed.  When updating the status table, we
        do remove_all_status, then slowly add in the new status before
        doing the commit, so the table is not every empty/building if
        somebody checks it.
        """

        session = meta.Session()
        entry = TableauProcess(agentid=agentid, name=name,
                               pid=pid, status=status)
        # We merge instead of add since 'tabadmin status -v' sometimes
        # returns duplicate lines.
        session.merge(entry)

    def get_tableau_status(self):
        try:
            return meta.Session().query(TableauProcess).\
                join(Agent).\
                filter(Agent.envid == self.envid).\
                filter(Agent.agent_type == 'primary').\
                filter(TableauProcess.name == 'Status').\
                one().status
        except NoResultFound:
            return TableauProcess.STATUS_UNKNOWN

    def _set_main_state(self, prev_tableau_status, tableau_status, agent, body):
        prev_state = self.stateman.get_state()

        if tableau_status not in (TableauProcess.STATUS_RUNNING,
                                  TableauProcess.STATUS_STOPPED,
                                  TableauProcess.STATUS_DEGRADED):
            self.log.error("status-check: Unknown reported tableau_status " + \
                "from tableau: %s.  prev_state: %s", tableau_status, prev_state)
            return  # fixme: do something more drastic than return?

        if prev_state not in TRANSITIONS:
            self.log.error("status-check: prev state unexpected: %s",
                            prev_state)
            return  # fixme: do something more drastic than return?

        # Get our new state and events to send based on the previous
        # state and new tableau status.
        new_state_info = TRANSITIONS[prev_state][tableau_status]

        self.log.debug("status-check: prev_state: %s, new state info: %s, " + \
                       "prev_tableau_status %s, tableau_status: %s",
                       prev_state, str(new_state_info),
                       prev_tableau_status, tableau_status)

        if 'state' in new_state_info and \
                                        new_state_info['state'] != prev_state:
            self.stateman.update(new_state_info['state'])

        if 'events' not in new_state_info:
            events = []
        else:
            events = new_state_info['events']
        if type(events) == type(EventControl.INIT_STATE_STARTED):
            events = [events]

        self._send_events(events, agent, body)

        if 'maint-stop' in new_state_info:
            # Make sure the maint server(s) are stopped if tableau
            # is not stopped.  For example, the user stopped
            # tableau via 'tabadmin stop' and then restarted it with
            # 'tabadmin start' without going through the Palette UI.
            self.log.debug("status-check: May stop maint server. " + \
                           "prev_state: %s, new state info: %s, " + \
                           "prev_tableau_status %s, tableau_status: %s, " + \
                           "maint_started: %s",
                           prev_state, str(new_state_info),
                           prev_tableau_status, tableau_status,
                           str(self.server.maint_started))

            if not self.server.maint_started:
                self.log.debug("state-check: maint server not running")
                return

            self.server.maint("stop")

        if 'maint-start' in new_state_info:
            # Make sure the maint server(s) are started if tableau
            # is stopped.  For example, the user stopped
            # tableau via 'tabadmin stop' and then the controller
            # started at that point (small chance, but possible).
            # We want to set the maint_started status.
            # We assume the user wanted the maint server started,
            # but can't be sure.
            self.log.debug("status-check: Will start maint server. " + \
                           "prev_state: %s, new state info: %s, " + \
                           "prev_tableau_status %s, tableau_status: %s, " + \
                           "maint_started: %s",
                           prev_state, str(new_state_info),
                           prev_tableau_status, tableau_status,
                           str(self.server.maint_started))

            if self.server.maint_started:
                self.log.debug("state-check: maint server already running")
                return

            self.server.maint("start")

    def _send_events(self, events, agent, body):
        """Send the events according to the old and new states.
           However, don't send DEGRADED-related events until
           Tableau has a chance to recover, since that's what it does."""
        if events:
            data = agent.todict()

        new_degraded_event = False
        for event in events:
            if event == EventControl.STATE_STARTED_AFTER_DEGRADED and \
                                        not self.sent_degraded_event:
                # We were degraded, and are running now, but never
                # sent out a degraded event, so don't send a
                # "no more degraded" event either.
                continue

            if event != EventControl.STATE_DEGRADED:
                self.server.event_control.gen(event, data)

                if event == EventControl.INIT_STATE_DEGRADED:
                    # If this is an "INIT_STATE_*" event, we send it,
                    # even if it is degraded.
                    self.sent_degraded_event = False
                continue

            new_degraded_event = True

            # Don't send the DEGRADED event until a minimum period of time
            # has elapsed with the state still DEGRADED.
            if not self.first_degraded_time:
                # Remember the time of the first DEGRADED state.
                self.first_degraded_time = time.time()
                continue

            if self.sent_degraded_event:
                # Already sent the degraded event
                continue

            try:
                event_degraded_min = \
                    int(self.server.system.get('event-degraded-min'))
            except ValueError:
                event_degraded_min = self.EVENT_DEGRADED_MIN_DEFAULT

            now = time.time()
            self.log.debug("status-check: now %d, first %d, min %d, diff %d",
                           now, self.first_degraded_time,
                           event_degraded_min,
                           now - self.first_degraded_time)
            if now - self.first_degraded_time >= event_degraded_min:
                self.log.debug("status-check: Sending degraded")
                self.server.event_control.gen(event,
                                      dict(body.items() + data.items()))
                self.sent_degraded_event = True

        if not new_degraded_event:
            self.first_degraded_time = None
            self.sent_degraded_event = False

    def run(self):
        try:
            self.tableau_status_loop()
        except (SystemExit, KeyboardInterrupt, GeneratorExit):
            raise
        except BaseException:
            line = traceback_string(all_on_one_line=False)
            self.server.event_control.gen(EventControl.SYSTEM_EXCEPTION,
                                      {'error': line,
                                       'version': self.server.version})
            self.log.error("status-check: Fatal: " + \
                           "Exiting tableau_status_loop on exception.")
            # pylint: disable=protected-access
            os._exit(93)

    def tableau_status_loop(self):
        while True:
            self.log.debug("status-check: About to timeout or " + \
                           "wait for a new primary to connect")
            try:
                status_request_interval = \
                    int(self.server.system.get('status-request-interval'))
            except ValueError:
                status_request_interval = \
                                self.STATUS_REQUEST_INTERVAL_DEFAULT

            new_primary = self.manager.check_status_event.wait(
                                        status_request_interval)

            self.log.debug("status-check: new_primary: %s", new_primary)
            if new_primary:
                self.manager.clear_check_status_event()

            session = meta.Session()
            try:
                # Don't do a 'tabadmin status -v' if upgrading
                acquired = self.rwlock.read_acquire(blocking=False)
                if not acquired:
                    self.log.debug("status-check: Upgrading.  Won't run.")
                    continue
                self.check_status()
            finally:
                if acquired:
                    self.rwlock.read_release()
                session.rollback()
                meta.Session.remove()

    def check_status(self):

        self.log.setLevel(self.st_config.debug_level)
        # FIXME: Tie agent to domain.
        agent = self.manager.agent_by_type(AgentManager.AGENT_TYPE_PRIMARY)
        if not agent:
            self.log.debug("status-check: The primary agent is either " + \
                           "not connected or not enabled.")
            return

        aconn = agent.connection
        if not aconn:
            session = meta.Session()
            self.log.debug(
                    "status-check: No primary agent currently connected.")
            self.remove_all_status()
            session.commit()
            return

        # Don't do a 'tabadmin status -v' if the user is doing an action.
        acquired = aconn.user_action_lock(blocking=False)
        if not acquired:
            self.log.debug(
                "status-check: Primary agent locked for user action. " + \
                "Skipping status check.")
            return

        # We don't force the user to delay starting their request
        # until the 'tabadmin status -v' is finished.
        aconn.user_action_unlock()

        self.check_status_with_connection(agent)

    def _systeminfo_parse(self, agent, systeminfo_xml):
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        """Returns:
                SYSTEMINFO_SUCCESS if getting status via systeminfo is fine.

            Raises an exception if there is a problem with systeminfo.
        """
        self.log.debug("_systeminfo_parse: Received: %s", systeminfo_xml)
        try:
            root = ET.fromstring(systeminfo_xml)
        except ET.ParseError as ex:
            self.log.error(
                    "_systeminfo_parse: xml parse error: '%s' from '%s':",
                    str(ex), systeminfo_xml)
            raise SysteminfoException(SysteminfoError.PARSE_FAILURE,
                                       "xml parse error: '%s'" % (str(ex)))

        if root.tag != 'systeminfo':
            self.log.error("_systeminfo_parse: wrong root tag: %s", root.tag)
            raise SysteminfoException(SysteminfoError.PARSE_FAILURE,
                                      "wrong root tag: %s" % root.tag)

        session = meta.Session()
        prev_tableau_status = self.get_tableau_status()

        self.remove_all_status()

        tableau_status = None

        failed_proc_str = ""
        for child in root:
            if child.tag == 'machines':
                for machine in child:
#                    print "machine:", machine.attrib
                    if not 'name' in machine.attrib:
                        self.log.error("_systeminfo_parse: missing " + \
                                       "'name' in machine attribute: %s",
                                       str(machine.attrib))
                        raise SysteminfoException(SysteminfoError.PARSE_FAILURE,
                                       ("missing " + \
                                       "'name' in machine attribute: %s") % \
                                       str(machine.attrib))

                    host = machine.attrib['name']
                    agentid = Agent.get_agentid_from_host(self.envid, host)

                    if not agentid:
                        self.log.error("_systeminfo_parse: No such" + \
                                       " agent host known (yet/any more?): %s",
                                       host)
                        continue

                    machine_agent = Agent.get_by_id(agentid)
                    if machine_agent:
                        machine_displayname = machine_agent.displayname
                    else:
                        machine_displayname = "Unknown"

                    for info in machine:
                        #print "    ", info.tag, "attributes:", info.attrib
                        service_name = info.tag
                        if not 'status' in info.attrib:
                            self.log.error("_systeminfo_parse: missing " + \
                                           "'status' in machine %s attrib: %s",
                                           host, str(info.attrib))
                            raise SysteminfoException(
                                      SysteminfoError.PARSE_FAILURE,
                                      ("missing " + \
                                      "'status' in machine %s attrib: %s") % \
                                      (host, str(info.attrib)))

                        if 'worker' in info.attrib:
                            worker_info = info.attrib['worker']
                            parts = worker_info.split(':')
                            if len(parts) == 1 or not parts[1].isdigit():
                                # port = -2
                                self.log.error("_systeminfo_parse: missing " + \
                                               "':' or not an integer in "
                                               "machine %s for " + \
                                               "worker: %s", host,
                                               str(worker_info))

                                raise SysteminfoException(
                                               SysteminfoError.PARSE_FAILURE,
                                               ("Missing " + \
                                               "':' or not an integer in "
                                               "machine %s for " + \
                                               "worker: %s") % \
                                               (host, str(worker_info)))
                            else:
                                port = int(parts[1])

                        service_status = info.attrib['status']
#                        print "service_name:", service_name, "port", port
                        if service_status not in ('Active', 'Passive', 'Busy',
                                                 'ReadOnly', 'ActiveSyncing'):
                            # Keep track of failed tableau processes
                            failed_proc_str += ("Machine %s: Process %s is "
                                                 "%s\n") % \
                                                 (machine_displayname,
                                                 service_name, service_status)

                        self._add(agentid, service_name, port, service_status)
                        self.log.debug("system_info_parse: logged: " + \
                                       "%d, %s, %d, %s",
                                       agentid, service_name, port,
                                       service_status)
            elif child.tag == 'service':
#                print "service:",
                info = child.attrib
                if not 'status' in info:
                    self.log.error("_systeminfo_parse: Missing 'status': %s",
                                    str(info))
                    raise SysteminfoException(SysteminfoError.PARSE_FAILURE,
                                              "Missing 'status': %s" % \
                                              str(info))

                #print "    status:", info['status']
                tableau_status = info['status']
                if tableau_status in ('Down', 'DecommisionedReadOnly',
                    'DecomisioningReadOnly', 'DecommissionFailedReadOnly'):
                    tableau_status = TableauProcess.STATUS_DEGRADED
                elif tableau_status in ('Active', 'Passive',
                                        'Busy', 'ReadOnly', 'ActiveSyncing'):
                    tableau_status = TableauProcess.STATUS_RUNNING
                elif tableau_status in ('StatusNotAvailable',
                                        'StatusNotAvailableSyncing'):
                    tableau_status = TableauProcess.STATUS_UNKNOWN
                else:
                    self.log.error("_systeminfo_parse: Unexpected status: '%s'",
                                  tableau_status)
                    tableau_status = TableauProcess.STATUS_UNKNOWN

                # Note: The status can never be STOPPED since if Tableau
                # is stopped, then it won't respond to the systeminfo
                # GET URL.
                self._add(agent.agentid, "Status", 0, tableau_status)
            else:
                self.log.error("_systeminfo_parse: Unexpected child.tag: '%s'",
                    child.tag)

        if tableau_status is None:
            self.log.error(
                        "_systeminfo_parse: Tableau status not valid: %s",
                       str(systeminfo_xml))
            session.rollback()
            raise SysteminfoException(SysteminfoError.PARSE_FAILURE,
                                      "Tableau status not valid")

        if failed_proc_str:
            # Failed process(es) for the event
            body = {'info': failed_proc_str}
        else:
            body = None

        self._finish_status(agent, tableau_status, prev_tableau_status, body)
        return self.SYSTEMINFO_SUCCESS

    def _systeminfo_url(self):
        """For now, start with the tableau-server-url, and replace the
           hostname with 127.0.0.1.  Eventually we need to look at the
           yml, gateway.hosts, ssl.enabled, gateway.ports, and
           decided both the URL and which host should request systeminfo.
           (The gateway/web server may not be on the primary.)

           Returns None if no valid url is available.
        """

        systeminfo_url = self.st_config.tableau_server_url
        if not systeminfo_url:
            self.log.error("_systeminfo_get: no url configured.")
            return None

        result = urlparse(systeminfo_url)

        if not result.scheme:
            self.log.error("_systeminfo_get: Bad url: %s", systeminfo_url)
            return None

        if result.port:
            url = "%s://127.0.0.1:%d/admin/systeminfo.xml" % \
                                            (result.scheme, result.port)
        else:
            url = "%s://127.0.0.1/admin/systeminfo.xml" % (result.scheme)

        return url

    def _systeminfo_get(self, agent):
        # pylint: disable=too-many-return-statements
        """Returns:
            - The xml on success
            Raises SysteminfoException on error.
        """

        url = self._systeminfo_url()

        systeminfo_timeout_ms = self.st_config.status_systeminfo_timeout_ms

        try:
            res = agent.connection.http_send_get(url,
                                                 timeout=systeminfo_timeout_ms)
        except (socket.error, IOError, exc.HTTPException,
                                                httplib.HTTPException) as ex:
            self.log.info("_systeminfo_get %s failed: %s",
                          url, str(ex))
            raise SysteminfoException(SysteminfoError.COMM_FAILURE,
                                      "_systeminfo_get %s failed: %s" % \
                                      (url, str(ex)))

        content_type = res.getheader('Content-Type', '').lower()

        self.server.log.info("GET %s, Headers: '%s'",
                             url, str(res.getheaders()))

        if content_type == 'application/x-json':
            # This extended type indicates the agent generated the JSON,
            # i.e. there was an error.
            try:
                data = json.loads(res.body)
            except ValueError as ex:
                self.log.error("_systeminfo_get: Bad json returned for %s: %s",
                               url, res.body)
                raise SysteminfoException(SysteminfoError.JSON_PARSE_FAILURE,
                                          "Invalid json returned for %s: %s" % \
                                          (url, res.body))

            self.log.info("_systeminfo_get: get %s reported failed: %s",
                           url, data)
            if 'error' in data:
                if data['error'].find(
                              "Unable to connect to the remote server") != -1:
                    # We had the tableau URL and it wasn't answering.
                    # Tableau is probably down, though could be the
                    # wrong URL/port.
                    raise SysteminfoException(SysteminfoError.CONNECT_FAILURE,
                                        ("HTTP GET %s reported failed: %s") % \
                                        (url, data['error']))

                if data['error'].find('The operation has timed out') != -1:
                    raise SysteminfoException(SysteminfoError.COMM_TIMEDOUT,
                            "HTTP GET Timed out after %.1f seconds on %s" % \
                                    (systeminfo_timeout_ms/1000., url))

                if 'status-code' in data and data['status-code'] == 404:
                    raise SysteminfoException(SysteminfoError.NOT_FOUND,
                                        ("Page not found: %s") % (url))

            raise SysteminfoException(SysteminfoError.UNEXPECTED_RESPONSE,
                            "Unexpected response error: %s" % str(data))

        return res.body

    def _set_status_stopped(self, agent):
        """systeminfo is enabled in tableau, so if it is failing now,
           assume tableau is stopped."""

        prev_tableau_status = self.get_tableau_status()
        self.remove_all_status()
        name = "Status"
        pid = 0
        tableau_status = TableauProcess.STATUS_STOPPED
        self._add(agent.agentid, name, 0, tableau_status)
        self.log.debug("_set_status_stopped: logged: %s, %d, %s",
                       name, pid, tableau_status)

        self._finish_status(agent, tableau_status, prev_tableau_status,
                {'stdout': 'systeminfo failed.  Assuming Tableau is stopped.'})

    def _tableau_systeminfo_enabled(self):
        """Returns:
            True:   The Tableau configuration has systeminfo enabled.
            False:  The Tableau configuration for systeminfo is disabled."""

        yml_val = self.server.yml.get(
                    'wgserver.systeminfo.allow_referrer_ips',
                    default='')

        if yml_val.find('127.0.0.1') != -1 or yml_val.find('localhost') != -1:
            return True

        return False

    def check_status_with_connection(self, agent):
        tableau_systeminfo_enabled = self._tableau_systeminfo_enabled()

        data = {}

        systeminfo_url = self._systeminfo_url()

        tableau_version = YmlEntry.get(self.envid, 'version.external',
                                                                default='8')
        if systeminfo_url and tableau_version[0:1] == '9' and \
                self.st_config.status_systeminfo and tableau_systeminfo_enabled:
            try:
                # Returns the xml on success
                xml_result = self._systeminfo_get(agent)

                # Remember this URL worked
                self.systeminfo_url_worked = systeminfo_url

                self._systeminfo_parse(agent, xml_result)    # parse the xml

                # Send an event if appropriate
                self._systeminfo_eventit(agent, data, systeminfo_url)

                return

            except SysteminfoException as ex:
                prev_state = self.stateman.get_state()
                if ex.errnum == SysteminfoError.NOT_FOUND and \
                            self.systeminfo_url_worked == systeminfo_url and \
                            prev_state in (StateManager.STATE_STOPPED,
                                             StateManager.STATE_STOPPING):
                    # Could be the maintenance web server responding with
                    # "Not found" since and tableau is stopped.
                    self._set_status_stopped(agent)
                    self.log.info("_system_info: Page not found and "
                        "it previously worked, but the state was %s "
                        "so not sending systeminfo event.", prev_state)
                    return
                elif ex.errnum == SysteminfoError.CONNECT_FAILURE:
                    self.log.info("_system_info: failed to connect")

                    # Be as confident as possible that tableau really is stopped
                    # and the user didn't configure the tableau-server-url
                    # wrong.  The tableau-server-url derived url has to work
                    # at least once with systeminfo # before the failure to
                    # get systeminfo should mean that tableau is really stopped.
                    if self.systeminfo_url_worked == systeminfo_url:
                        self.log.error("status-check: systeminfo failed while "
                                       "enabled in tableau: assuming tableu is "
                                       "stopped.")
                        self._set_status_stopped(agent)
                        data['info'] = "Systeminfo failed to connect, but " + \
                                       "connect previously worked.  " + \
                                       "Assuming Tableau is stopped."

                        self._systeminfo_eventit(agent, data, systeminfo_url)
                        return

                # systeminfo didn't work, but we don't know if tableau
                # being down is the cause.  The exception could be due to
                # a parse error, bad url, timeout, etc.
                data['error'] = ex.message
                if ex.errnum == SysteminfoError.PARSE_FAILURE:
                    # Add the raw XML to the error.
                    data['error'] += ' XML: ' + str(xml_result)
                self._systeminfo_eventit(agent, data, systeminfo_url)

                if self.st_config.status_systeminfo_only:
                    self.log.info("systeminfo failed but not allowed to use "
                                  "tabadmin status -v")
                    self._set_status_unknown(agent,
                                "systeminfo failed but configured to not "
                                 "allow use of tabadmin status -v")
                    return

        # Get tableau status via 'tabadmin status -v' instead.
        self._get_status_tabadmin(agent)
        return

    def _set_status_unknown(self, agent, body):
        """Remove all status and set tableau status to UNKNOWN."""

        prev_tableau_status = self.get_tableau_status()
        self.remove_all_status()
        tableau_status = TableauProcess.STATUS_UNKNOWN
        self._add(agent.agentid, "Status", 0, tableau_status)
        self._finish_status(agent, tableau_status, prev_tableau_status, body)

    def _systeminfo_eventit(self, agent, data, systeminfo_url):
        """Send if event failed/okay event as appropriate."""

        notification = self.server.notifications.get("systeminfo")

        if success(data):
            if notification.color == 'red':
                adata = agent.todict()
                if 'info' in data:
                    adata['info'] = data['info']
                if self.st_config.status_systeminfo_send_alerts:
                    self.server.event_control.gen(
                                EventControl.SYSTEMINFO_OKAY, adata)
                notification.modification_time = func.now()
                notification.color = 'green'
                notification.description = systeminfo_url
                meta.Session.commit()
        else:
            # Failed
            if notification.color != 'red' or \
                                notification.description != systeminfo_url:
                # If the systeminfo_url has changed, then tell them this
                # one didn't work (either).  We can potentially send
                # multiple of these events if they keep entering bad
                # URLs.
                adata = agent.todict()
                adata['error'] = data['error']
                if self.st_config.status_systeminfo_send_alerts:
                    self.server.event_control.gen(
                            EventControl.SYSTEMINFO_FAILED, adata)
                notification.modification_time = func.now()
                notification.color = 'red'
                notification.description = systeminfo_url
                meta.Session.commit()

    def _get_status_tabadmin(self, agent):
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements

        """Try to get tableau status the old-fashioned way via
            'tabadmin status -v'.
        """

        agentid = agent.agentid

        body = self.server.status_cmd(agent)
        if 'error' in body:
            self.log.error(
                "status-check: Error from tabadmin status command: %s",
                str(body))
            return

        if 'exit-status' in body:
            if body['exit-status']:
                self.log.error("status-check: Failed exit status: %d for " + \
                               "tabadmin status command: %s",
                               body['exit-status'], str(body))
                return
        else:
            self.log.error("status-check: Missing exit-status from " + \
                           "tabadmin status command: %s", str(body))
            return

        if not body.has_key('stdout'):
            # fixme: Probably update the status table to say
            # something's wrong.
            self.log.error("status-check: No output received for " + \
                           "status monitor. body: " + str(body))
            return

        stdout = body['stdout']
        lines = string.split(stdout, '\n')

        session = meta.Session()

        prev_tableau_status = self.get_tableau_status()

        self.remove_all_status()
        # Do not commit until after the table is added to.
        # Otherwise, the table could be empty temporarily.

        tableau_status = None
        failed_proc_str = ""
        machine_agent = Agent.get_by_id(agentid)
        if machine_agent:
            machine_displayname = machine_agent.displayname
        else:
            machine_displayname = "Unknown"
        for line in lines:
            line = line.strip()
            parts = line.split(' ')

            # 'Tableau Server Repository Database' (1764) is running.
            if parts[0] == "'Tableau" and parts[1] == 'Server':
                if agentid:
                    pattern = r"'Tableau Server (?P<service>.*)'" + \
                              r"\s(\((?P<pid>[0-9]*)\))?(status)?\s?" + \
                              r"is\s(?P<status>.*)\."
                    match = re.search(pattern, line)
                    if not match:
                        self.log.debug("status-check: unmatched line: %s",
                                        line)
                        continue

                    service = match.group('service')        # "Repository"
                    if not 'service':
                        self.log.debug("status-check: empty service in " + \
                                       "line: %s", line)
                        continue

                    pid_str = match.group('pid')   # "1764"
                    if pid_str:
                        try:
                            pid = int(pid_str)
                        except StandardError:
                            self.log.error("status-check: Bad PID: " + pid_str)
                            continue
                    else:
                        pid = -2

                    status = match.group('status') # "running" or "running..."
                    if not 'status':
                        self.log.debug("status-check: empty 'status' " + \
                                       "in line: %s", line)
                        continue

                    self._add(agentid, service, pid, status)
                    self.log.debug("status-check: logged: %s, %d, %s", service,
                                   pid, status)

                    if status.find('running') == -1:
                        # Keep track of failed tableau processes
                        failed_proc_str += ("Machine %s: Process %s is "
                                            "%s\n") % \
                                            (machine_displayname,
                                            service, status)
                else:
                    # FIXME: log error
                    pass
            elif parts[0] == 'Status:':
                server_status = parts[1].strip()
                if agentid:
                    self._add(agentid, "Status", 0, server_status)
                    if tableau_status == None or server_status == 'DEGRADED':
                        tableau_status = server_status
                else:
                    # FIXME: log error
                    pass
            else:
                line = line.strip()
                if line[-1:] == ':':
                    # A hostname or IP address is specified: new section
                    host = parts[0].strip().replace(':', '')
                    agentid = Agent.get_agentid_from_host(self.envid, host)
                    machine_agent = Agent.get_by_id(agentid)
                    if machine_agent:
                        machine_displayname = machine_agent.displayname
                    else:
                        machine_displayname = "Unknown"
                else:
                    # Examples:
                    #   "Connection error contacting worker 1"
                    #   'Tableau Server Cluster Controller' is stopped.
                    #   'Tableau Server Repository' status is not available.
                    #   'Tableau Server File Store' status is not available.
                    if not agentid:
                        self.log.debug("status-check: Can't log due to " + \
                                       "unknown or disabled agent: %s, %d, %s",
                                       line, -1, 'error')
                    else:
                        self._add(agentid, line, -1, 'error')
                        self.log.debug("status-check: logged: %s, %d, %s",
                                       line, -1, 'error')

        if tableau_status is None:
            self.log.error("status-check: Tableau status not valid: %s",
                           str(lines))
            session.rollback()
            return

        if failed_proc_str:
            # Failed process(es) for the event
            body['info'] = failed_proc_str

        self._finish_status(agent, tableau_status, prev_tableau_status, body)

    def _finish_status(self, agent, tableau_status, prev_tableau_status, body):

        aconn = agent.connection
        acquired = aconn.user_action_lock(blocking=False)
        if not acquired:
            # If the user_action_lock is taken, that thread should
            # control the state.  We don't update the tableau process
            # table since state should be consistent with tableau process
            # status.
            self.log.debug(
                "status-check: Primary agent locked for user action " + \
                "after tabadmin status finished.  " + \
                "Will not update state or tableau status.")
            meta.Session.rollback()
            return

        self.log.debug("status-check: Logging main status: %s", tableau_status)
        self._set_main_state(prev_tableau_status, tableau_status, agent, body)

        meta.Session.commit()
        aconn.user_action_unlock()
