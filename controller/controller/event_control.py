from mako.template import Template
from mako import exceptions
import mako.runtime
mako.runtime.UNDEFINED="*UNDEFINED*"

from sqlalchemy import Column, Integer, BigInteger, String, Boolean
from sqlalchemy.schema import ForeignKey, UniqueConstraint
from sqlalchemy.orm.exc import NoResultFound
from akiri.framework.ext.sqlalchemy import meta
from profile import UserProfile

from mixin import BaseMixin

class EventControl(meta.Base, BaseMixin):
    __tablename__ = "event_control"

    eventid = Column(BigInteger, unique=True, nullable=False, \
                                   autoincrement=True, primary_key=True)

    # The unique event key for the subject and message templates.
    key = Column(String, unique=True, nullable=False)

    # level: E (Error), W (Warning) or I (Info)
    level = Column(String(1))

    # Whether or not to send email for this event
    send_email = Column(Boolean)

    # subject is a python key-value substitution template for the subject
    subject = Column(String)

    # event_description is a mako template for the event description
    event_description = Column(String)

    # email_message is a mako template for the email_message
    email_message = Column(String)

    icon = Column(String)
    color = Column(String)

    event_type = Column(String) # backup, restore, etc.

    # event keys
    INIT_STATE_STARTED="INIT-STATE-STARTED"
    INIT_STATE_STOPPED="INIT-STATE-STOPPED"
    INIT_STATE_DEGRADED="INIT-STATE-DEGRADED"

    STATE_STARTED="STATE-STARTED"
    STATE_STOPPED="STATE-STOPPED"
    STATE_DEGRADED="STATE-DEGRADED"

    BACKUP_STARTED="BACKUP-STARTED"
    BACKUP_FINISHED="BACKUP-FINISHED"
    BACKUP_FAILED="BACKUP-FAILED"

    BACKUP_BEFORE_STOP_STARTED="BACKUP-BEFORE-STOP-STARTED"
    BACKUP_BEFORE_STOP_FINISHED="BACKUP-BEFORE-STOP-FINISHED"
    BACKUP_BEFORE_STOP_FAILED="BACKUP-BEFORE-STOP-FAILED"

    BACKUP_BEFORE_RESTORE_STARTED="BACKUP-BEFORE-RESTORE-STARTED"
    BACKUP_BEFORE_RESTORE_FINISHED="BACKUP-BEFORE-RESTORE-FINISHED"
    BACKUP_BEFORE_RESTORE_FAILED="BACKUP-BEFORE-RESTORE-FAILED"

    RESTORE_STARTED="RESTORE-STARTED"
    RESTORE_FINISHED="RESTORE-FINISHED"
    RESTORE_FAILED="RESTORE-FAILED"

    TABLEAU_START_FAILED="TABLEAU-START-FAILED"

    MAINT_START_FAILED="MAINT-START-FAILED"
    MAINT_STOP_FAILED="MAINT-STOP-FAILED"

    MAINT_OFFLINE="MAINT-OFFLINE"
    MAINT_ONLINE="MAINT-ONLINE"

    ARCHIVE_START_FAILED="ARCHIVE-START-FAILED"
    ARCHIVE_STOP_FAILED="ARCHIVE-STOP-FAILED"

    AGENT_COMM_LOST="AGENT-COMM-LOST"
    AGENT_FAILED_STATUS="AGENT-FAILED-STATUS"
    AGENT_RETURNED_INVALID_STATUS="AGENT-RETURNED-INVALID-STATUS"

    AGENT_DISCONNECT="AGENT-DISCONNECT"

    #
    LICENSE_INVALID="LICENSE-INVALID"
    LICENSE_EXPIRED="LICENSE-EXPIRED"
    LICENSE_RENEWAL="LICENSE-RENEWAL"
    PERMISSION="PERMISSION"
    AGENT_COMMUNICATION="AGENT-COMMUNICATION"
    MAINT_WEB="MAINT-WEB"
    TABLEAU_USER_TABLE="TABLEAU-USER-TABLE"
    TABLEAU_SYSTEM_TABLE="TABLEAU-SYSTEM-TABLE"

    SCHEDULED_JOB_STARTED="SCHEDULE-JOB-STARTED"
    SCHEDULED_JOB_FAILED="SCHEDULE-JOB-FAILED"

    #
    EXTRACT_OK="EXTRACT-OK"
    EXTRACT_FAILED="EXTRACT-FAILED"

    ZIPLOGS_FAILED="ZIPLOGS-FAILED"
    CLEANUP_FAILED="CLEANUP-FAILED"
    SYNC_FAILED="SYNC_FAILED"

    FIREWALL_OPEN_FAILED="FIREWALL-OPEN-FAILED"

    DISK_USAGE_ABOVE_HIGH_WATERMERK="DISK-USAGE-ABOVE-HIGH-WATERMARK"
    DISK_USAGE_ABOVE_LOW_WATERMARK="DISK-USAGE-ABOVE-LOW-WATERMARK"
    DISK_USAGE_OKAY="DISK-USAGE-OKAY"

    # levels
    LEVEL_ERROR="E"
    LEVEL_WARNING="W"
    LEVEL_INFO="I"

    level_strings = {
        LEVEL_ERROR: "Error",
        LEVEL_WARNING: "Warning",
        LEVEL_INFO: "Info"
    }

    # event types
    TYPE_BACKUP="backup"
    TYPE_RESTORE="restore"
    TYPE_MAINT_SERVER="maint-server"
    TYPE_ARCHIVE_SERVER="archive-server"
    TYPE_STATUS="status"
    TYPE_AGENT="agent"
    TYPE_TABLEAU="tableau"
    TYPE_SCHED="sched"
    TYPE_EXTRACT="extract"

    @classmethod
    def types(cls):
        L = []
        for t in cls.__dict__:
            if t.startswith('TYPE_'):
                L.append(getattr(cls, t))
        return L

    defaults_filename = 'event_control.json'

class EventControlManager(object):
    DATEFMT = "%I:%M %p PDT on %B %d, %Y"

    def __init__(self, server):
        self.alert_email = server.alert_email
        self.indented = self.alert_email.indented
        self.log = server.log
        self.envid = server.environment.envid
        self.event = server.event

    def get_event_control_entry(self, key):
        try:
            entry = meta.Session.query(EventControl).\
                filter(EventControl.key == key).one()
        except NoResultFound, e:
            return None

        return entry

    def gen(self, key, data={}, userid=None, siteid=None, timestamp=None):
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

        event_entry = self.get_event_control_entry(key)
        if event_entry:
            subject = event_entry.subject
            event_description = event_entry.event_description
        else:
            self.log.error("No such event key: %s. data: %s\n", key, str(data))
            return

        if 'exit-status' in data:
            data['exit_status'] = data['exit-status']

        # The userid for extracts is the Tableau "system_users_id".
        # The userid for other events is the "userid".
        # (Both in the "users" table.)
        if not 'username' not in data and userid:
            if key == "EXTRACT-OK" or key == "EXTRACT-FAILED":
                user_profile = UserProfile.get_by_system_users_id(userid)
            else:
                user_profile = UserProfile.get(userid)

            if user_profile:
                if user_profile.friendly_name:
                    data['username'] = user_profile.friendly_name
                else:
                    data['username'] = user_profile.name

        # Use the data dict for template substitution.
        try:
            subject = subject % data
        except (ValueError, KeyError) as e:
            subject = "Template subject conversion failure: " + str(e) + \
                "subject: " + subject + \
                ", data: " + str(data)
        if event_description:
            try:
                mako_template = Template(event_description)
                event_description = mako_template.render(**data)
            except:
                event_description = \
                    "Mako template message conversion failure: " + \
                        exceptions.text_error_template().render() + \
                            "\ntemplate: " + event_description + \
                            "\ndata: " + str(data)
        else:
           event_description = self.make_default_description(data)

        # Log the event to the database
        self.event.add(key, subject, event_description, event_entry.level,
                       event_entry.icon, event_entry.color, 
                       event_entry.event_type, userid=userid, siteid=siteid,
                                                        timestamp=timestamp)

        if event_entry.send_email:
            self.alert_email.send(event_entry, data)

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
