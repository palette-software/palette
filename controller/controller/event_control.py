import sys, traceback
import datetime
from dateutil import tz
from mako.template import Template
from mako import exceptions
from mako.exceptions import MakoException
import mako.runtime

from sqlalchemy import Column, BigInteger, String, Boolean
from sqlalchemy.orm.exc import NoResultFound

# pylint: disable=import-error,no-name-in-module
from akiri.framework.ext.sqlalchemy import meta
# pylint: enable=import-error,no-name-in-module

from event import EventEntry
from general import SystemConfig
from profile import UserProfile
from util import DATEFMT, UNDEFINED, utc2local
from mixin import BaseMixin, BaseDictMixin
from manager import Manager

from sites import Site
from projects import Project

mako.runtime.UNDEFINED = UNDEFINED

import re

class EventControl(meta.Base, BaseMixin, BaseDictMixin):
    __tablename__ = "event_control"

    eventid = Column(BigInteger, unique=True, nullable=False,
                     autoincrement=True, primary_key=True)

    # The unique event key for the subject and message templates.
    key = Column(String, unique=True, nullable=False)

    # level: E (Error), W (Warning) or I (Info)
    level = Column(String(1))

    # Whether or not to send email for this event
    send_email = Column(Boolean)

    # subject is a python key-value substitution template for the
    # event's subject
    subject = Column(String)

    # event_description is a mako template for the event description
    event_description = Column(String)

    # email_subject is a python key-value substitution template for
    # the email message's subject
    email_subject = Column(String)

    # email_message is a mako template for the email_message
    email_message = Column(String)

    icon = Column(String)
    color = Column(String)

    event_type = Column(String) # backup, restore, etc.

    # Columns added to store descriptions and visiblity of events
    event_type_label = Column(String)
    event_label = Column(String)
    event_label_desc = Column(String)
    admin_visibility = Column(Boolean)
    publisher_visibility = Column(Boolean)

    # event keys
    INIT_STATE_STARTED = "INIT-STATE-STARTED"
    INIT_STATE_STOPPED = "INIT-STATE-STOPPED"
    INIT_STATE_DEGRADED = "INIT-STATE-DEGRADED"

    STATE_STARTED = "STATE-STARTED"
    STATE_STOPPED = "STATE-STOPPED"
    STATE_DEGRADED = "STATE-DEGRADED"
    STATE_STARTED_AFTER_DEGRADED = "STATE-STARTED-AFTER-DEGRADED"
    STATE_UNEXPECTED_STATE_STOPPED = "STATE-UNEXPECTED-STOPPED"
    STATE_UNEXPECTED_STATE_STARTED = "STATE-UNEXPECTED-STARTED"
    # pylint: disable=invalid-name
    STATE_UNEXPECTED_STOPPED_AFTER_DEGRADED = \
                                    "STATE-UNEXPECTED-STOPPED-AFTER-DEGRADED"

    BACKUP_STARTED = "BACKUP-STARTED"
    BACKUP_FINISHED = "BACKUP-FINISHED"
    BACKUP_FINISHED_COPY_FAILED = "BACKUP-FINISHED-COPY-FAILED"
    BACKUP_FAILED = "BACKUP-FAILED"

    BACKUP_STARTED_SCHEDULED = "BACKUP-STARTED-SCHEDULED"
    BACKUP_FINISHED_SCHEDULED = "BACKUP-FINISHED-SCHEDULED"
    BACKUP_FINISHED_SCHEDULED_COPY_FAILED = \
                                        "BACKUP-FINISHED-SCHEDULED-COPY-FAILED"
    BACKUP_FAILED_SCHEDULED = "BACKUP-FAILED-SCHEDULED"

    BACKUP_BEFORE_STOP_STARTED = "BACKUP-BEFORE-STOP-STARTED"
    BACKUP_BEFORE_STOP_FINISHED = "BACKUP-BEFORE-STOP-FINISHED"
    BACKUP_BEFORE_STOP_FINISHED_COPY_FAILED = \
                                    "BACKUP-BEFORE-STOP-FINISHED-COPY-FAILED"
    BACKUP_BEFORE_STOP_FAILED = "BACKUP-BEFORE-STOP-FAILED"

    BACKUP_BEFORE_RESTART_STARTED = "BACKUP-BEFORE-RESTART-STARTED"
    BACKUP_BEFORE_RESTART_FINISHED = "BACKUP-BEFORE-RESTART-FINISHED"
    BACKUP_BEFORE_RESTART_FINISHED_COPY_FAILED = \
                                "BACKUP-BEFORE-RESTART-FINISHED-COPY-FAILED"
    BACKUP_BEFORE_RESTART_FAILED = "BACKUP-BEFORE-RESTART-FAILED"

    BACKUP_BEFORE_RESTORE_STARTED = "BACKUP-BEFORE-RESTORE-STARTED"
    BACKUP_BEFORE_RESTORE_FINISHED = "BACKUP-BEFORE-RESTORE-FINISHED"
    BACKUP_BEFORE_RESTORE_FINISHED_COPY_FAILED = \
                                "BACKUP-BEFORE-RESTORE-FINISHED-COPY-FAILED"
    BACKUP_BEFORE_RESTORE_FAILED = "BACKUP-BEFORE-RESTORE-FAILED"

    RESTART_FINISHED = "RESTART-FINISHED"
    RESTART_FAILED = "RESTART-FAILED"

    RESTORE_STARTED = "RESTORE-STARTED"
    RESTORE_FINISHED = "RESTORE-FINISHED"
    RESTORE_FAILED = "RESTORE-FAILED"

    TABLEAU_START_FAILED = "TABLEAU-START-FAILED"

    MAINT_START_FAILED = "MAINT-START-FAILED"
    MAINT_STOP_FAILED = "MAINT-STOP-FAILED"

    MAINT_OFFLINE = "MAINT-OFFLINE"
    MAINT_ONLINE = "MAINT-ONLINE"

    ARCHIVE_START_FAILED = "ARCHIVE-START-FAILED"
    ARCHIVE_STOP_FAILED = "ARCHIVE-STOP-FAILED"

    AGENT_FAILED_STATUS = "AGENT-FAILED-STATUS"
    AGENT_RETURNED_INVALID_STATUS = "AGENT-RETURNED-INVALID-STATUS"

    AGENT_DISCONNECT = "AGENT-DISCONNECT"

    LICENSE_INVALID = "LICENSE-INVALID"
    LICENSE_EXPIRED = "LICENSE-EXPIRED"
    LICENSE_REPAIR_STARTED = "LICENSE-REPAIR-STARTED"
    LICENSE_REPAIR_FINISHED = "LICENSE-REPAIR-FINISHED"
    LICENSE_REPAIR_FAILED = "LICENSE-REPAIR-FAILED"

    PERMISSION = "PERMISSION"
    AGENT_COMMUNICATION = "AGENT-COMMUNICATION"
    MAINT_WEB = "MAINT-WEB"
    TABLEAU_USER_TABLE = "TABLEAU-USER-TABLE"
    TABLEAU_SYSTEM_TABLE = "TABLEAU-SYSTEM-TABLE"

    SCHEDULED_JOB_STARTED = "SCHEDULE-JOB-STARTED"
    SCHEDULED_JOB_FAILED = "SCHEDULE-JOB-FAILED"

    #
    EXTRACT_OK = "EXTRACT-OK"
    EXTRACT_FAILED = "EXTRACT-FAILED"

    ZIPLOGS_STARTED = "ZIPLOGS-STARTED"
    ZIPLOGS_FINISHED = "ZIPLOGS-FINISHED"
    ZIPLOGS_FAILED = "ZIPLOGS-FAILED"

    HTTP_BAD_STATUS = "HTTP-BAD-STATUS"
    HTTP_LOAD_WARN = "HTTP-LOAD-WARN"
    HTTP_LOAD_ERROR = "HTTP-LOAD-ERROR"

    CLEANUP_STARTED = "CLEANUP-STARTED"
    CLEANUP_FINISHED = "CLEANUP-FINISHED"
    CLEANUP_FAILED = "CLEANUP-FAILED"
    SYNC_FAILED = "SYNC_FAILED"

    FIREWALL_OPEN_FAILED = "FIREWALL-OPEN-FAILED"
    PORT_CONNECTION_FAILED = "PORT-CONNECTION-FAILED"
    PORT_CONNECTION_OKAY = "PORT-CONNECTION-OKAY"

    DISK_USAGE_ABOVE_HIGH_WATERMERK = "DISK-USAGE-ABOVE-HIGH-WATERMARK"
    DISK_USAGE_ABOVE_LOW_WATERMARK = "DISK-USAGE-ABOVE-LOW-WATERMARK"
    DISK_USAGE_OKAY = "DISK-USAGE-OKAY"

    CPU_LOAD_ABOVE_HIGH_WATERMARK = "CPU-LOAD-ABOVE-HIGH-WATERMARK"
    CPU_LOAD_ABOVE_LOW_WATERMARK = "CPU-LOAD-ABOVE-LOW-WATERMARK"
    CPU_LOAD_OKAY = "CPU-LOAD-OKAY"

    EMAIL_TEST = "EMAIL-TEST"

    WORKBOOK_ARCHIVE_FAILED = "WORKBOOK-ARCHIVE-FAILED"

    SYSTEM_EXCEPTION = "SYSTEM-EXCEPTION"
    PALETTE_UPDATED = "PALETTE-UPDATED"
    CONTROLLER_STARTED = "CONTROLLER-STARTED"

    # levels
    LEVEL_ERROR = "E"
    LEVEL_WARNING = "W"
    LEVEL_INFO = "I"

    level_strings = {
        LEVEL_ERROR: "Error",
        LEVEL_WARNING: "Warning",
        LEVEL_INFO: "Info"
    }

    # event types
    all_types = {
        'agent' : 'Palette Agent',
        'backup': 'Tableau Backup',
        'cleanup' : 'Tableau Log Cleanup',
        'communication' : 'Communication',
        'extract' : 'Extracts',
        'network': 'Network Test',
        'http' : 'HTTP Status',
        'license' : 'Licensing',
        'load' : 'Tableau Page Load',
        'logs' : 'Tableau Ziplog',
        'maintenance' : 'Maintenance Page',
        'restore' : 'Tableau Restore',
        'server' : 'Palette Server',
        'storage' : 'Storage',
        'cpu' : 'CPU Load',
        'tableau' : 'Tableau App',
        'workbook' : 'Workbooks'
    }

    @classmethod
    def types(cls):
        return cls.all_types

    defaults_filename = 'event_control.json'


class EventControlManager(Manager):

    def __init__(self, server):
        super(EventControlManager, self).__init__(server)
        self.alert_email = server.alert_email
        self.indented = self.alert_email.indented
        self.log = server.log
        self.envid = server.environment.envid

    def get_event_control_entry(self, key):
        try:
            entry = meta.Session.query(EventControl).\
                filter(EventControl.key == key).one()
        except NoResultFound:
            return None

        return entry

    def gen(self, key, data=None, userid=None, site_id=None, timestamp=None):
        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches

        """Generate an event.
            Arguments:
                key:    The key to look up.

                data:   A Dictionary with all of the event information.
                        Recognized keys:
                            - From http response:
                                stdout
                                stderr
                                xid
                                pid
                                exit-status
                                run-status
                                timestamp
                            - Sometimes added:
                                error
                                info
                            - Available from AgentConnection:
                                displayname
                                agent_type
                                uuid
                                auth, which has:
                                    hostname
                                    ip-address
                                    version
                                    listen-port
                                    install-dir
        """

        if data == None:
            data = {}

        if 'enabled' in data and not data['enabled']:
            self.log.debug("Agent is disabled so no event will be " + \
                           "generated.  key: %s, data: %s", key, data)
            return

        event_entry = self.get_event_control_entry(key)
        if event_entry:
            subject = event_entry.subject
            event_description = event_entry.event_description
        else:
            self.log.error("No such event key: %s. data: %s\n", key, str(data))
            return

        # add all system table entries to the data dictionary.
        data = dict(data.items() + self.server.system.todict().items())

        self.log.debug(key + " DATA: " + str(data))

        if 'exit-status' in data:
            data['exit_status'] = data['exit-status']
            del data['exit-status']

        # FIXME: remove when browser-aware timezone support is available.
        if timestamp is None:
            timestamp = datetime.datetime.now(tz=tz.tzlocal())
            self.log.debug(key + " timestamp : " + timestamp.strftime(DATEFMT))
        data['timestamp'] = timestamp.strftime(DATEFMT)

        # The userid for other events is the Palette "userid".
        profile = None
        if not 'username' in data and userid != None:
            profile = UserProfile.get(self.envid, userid)

        if not profile is None:
            data['username'] = profile.display_name()
            if profile.email:
                data['email'] = profile.email

        if not 'username' in data:
            data['username'] = mako.runtime.UNDEFINED

        data['event_type'] = event_entry.event_type
        data['event_type_label'] = event_entry.event_type_label
        data['event_label'] = event_entry.event_label
        data['event_label_desc'] = event_entry.event_label_desc
        data['admin_visibility'] = event_entry.admin_visibility
        data['publisher_visiblity'] = event_entry.publisher_visibility

        # set server-url(s)
        data['server_url'] = self.server.system.get(SystemConfig.SERVER_URL,
                                                    default='localhost')

        url = self.server.public_url()
        if url:
            data['tableau_server_url'] = url

        data['disk_watermark_low'] \
            = self.server.system.get('disk-watermark-low', default='')
        data['disk_watermark_high'] \
            = self.server.system.get('disk-watermark-high', default='')

        data['cpu_load_warn'] \
            = self.server.system.get('cpu-load-warn', default='')
        data['cpu_load_error'] \
            = self.server.system.get('cpu-load-error', default='')

        if not 'environment' in data:
            data['environment'] = self.server.environment.name

        if 'site_id' in data and 'site' not in data:
            site = Site.get_name_by_id(self.envid, data['site_id'])
            if not site is None:
                data['site'] = site
        if 'project_id' in data and 'project' not in data:
            project = Project.get_name_by_id(self.envid, data['project_id'])
            if not project is None:
                data['project'] = project

        # Create the row to get the eventid before doing subject/description
        # substitution.
        session = meta.Session()
        entry = EventEntry(complete=False, key='incomplete')
        session.add(entry)
        session.commit()

        data['eventid'] = entry.eventid

        # Use the data dict for template substitution.
        try:
            subject = subject % data
        except (ValueError, KeyError) as ex:
            subject = "Template subject conversion failure: " + str(ex) + \
                      "subject: " + subject + \
                      ", data: " + str(data)

        if event_description:
            try:
                mako_template = Template(event_description,
                                         default_filters=['h'])
                event_description = mako_template.render(**data)
            except MakoException:
                event_description = \
                    "Mako template message conversion failure: " + \
                        exceptions.text_error_template().render() + \
                            "\ntemplate: " + event_description + \
                            "\ndata: " + str(data)
        else:
            event_description = self.make_default_description(data)

        event_description = re.sub("(\n|\r\n){3,}", "\n\n", event_description)
        if not event_description.endswith("\n"):
            event_description = event_description + "\n"

        if self.server.event_debug:
            event_description = event_description + "--------\n" + str(data)

        # FIXME: remove when browser-aware timezone support is available.
        if timestamp.tzinfo is None:
            # if not timezone is specified, assume UTC.
            summary = utc2local(timestamp).strftime(DATEFMT)
        else:
            summary = timestamp.strftime(DATEFMT)

        # Log the event to the database
        entry.complete = True
        entry.key = key
        entry.envid = self.envid
        entry.title = subject
        entry.description = event_description
        entry.level = event_entry.level
        entry.icon = event_entry.icon
        entry.color = event_entry.color
        entry.event_type = event_entry.event_type
        entry.summary = summary
        entry.userid = userid
        entry.site_id = site_id
        entry.timestamp = timestamp

        session.merge(entry)
        session.commit()

        if event_entry.send_email:
            try:
                self.alert_email.send(event_entry, data)
            except StandardError:
                exc_traceback = sys.exc_info()[2]
                tback = ''.join(traceback.format_tb(exc_traceback))
                report = "Error: %s.  Traceback: %s" % (sys.exc_info()[1],
                                                        tback)

                self.log.error(("alert_email: Failed for event '%s', ' + \
                                 data '%s'.  Will not send email. %s"),
                                     event_entry.key, str(data), report)

    def make_default_description(self, data):
        """Create a default event message given the incoming dictionary."""

        description = ""

        if data.has_key('username'):
            description += "Requested by user: %s\n" % data['username']

        if data.has_key('displayname'):
            description += "Agent: %s\n" % data['displayname']

        if data.has_key('error'):
            description += self.indented("Error", data['error']) + '\n'

        if data.has_key('info') and data['info']:
            description += \
                self.indented("Additional information", data['info']) + '\n'

        # Include stderr, unless it is a duplicate of data['error']
        if data.has_key('stderr'):
            if not data.has_key('error') or (data['stderr'] != data['error']):
                description += self.indented('Error', data['stderr'])

        # Include stdout
        if data.has_key('stdout'):
            description += self.indented("Output", data['stdout'])

        return description
