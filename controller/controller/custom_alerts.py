import sqlalchemy
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, func
from sqlalchemy.schema import ForeignKey, UniqueConstraint
from sqlalchemy.orm.exc import NoResultFound
import meta

class CustomAlertsEntry(meta.Base):
    __tablename__ = "custom_alerts"

    alertid = Column(BigInteger, unique=True, nullable=False, \
                                   autoincrement=True, primary_key=True)

    # The unique alert key for the subject and message templates.
    key = Column(String, unique=True, nullable=False)

    # subject is a python key-value substitution template for the subject
    subject = Column(String) # The custom message for the 'key'.

    # message is a mako template for the message
    message = Column(String)

    def __init__(self, key, subject, message=None):
        self.key = key
        self.subject = subject
        self.message = message

class CustomAlerts(object):

    INIT_STATE_STARTED="INIT-STATE-STARTED"
    INIT_STATE_STOPPED="INIT-STATE-STOPPED"
    INIT_STATE_DEGRADED="INIT-STATE-DEGRADED"

    STATE_STARTED="STATE-STARTED"
    STATE_STOPPED="STATE-STOPPED"
    STATE_DEGRADED="STATE-DEGRADED"

    BACKUP_STARTED="BACKUP-STARTED"
    BACKUP_FINISHED="BACKUP-FINISHED"
    BACKUP_FAILED="BACKUP-FAILED"

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

    def get_alert(self, key):

        try:
            entry = meta.Session.query(CustomAlertsEntry).\
                filter(CustomAlertsEntry.key == key).one()
        except NoResultFound, e:
            return None

        return entry

    def populate(self):
        """Populate the initial custom alerts table if it is empty."""

        # fixme: Init the custom alerts elsewhere.
        entries = [
            (CustomAlerts.INIT_STATE_STARTED,
                        'Controller started.  Initial tableau state: started'),
            (CustomAlerts.INIT_STATE_STOPPED,
                        'Controller started.  Initial tableau state: stopped'),
            (CustomAlerts.INIT_STATE_DEGRADED,
                        'Controller started. Initial tableau state: degraded'),
            (CustomAlerts.STATE_STARTED, 'Tableau server started'),
            (CustomAlerts.STATE_STOPPED, 'Tableau server stopped'),
            (CustomAlerts.STATE_DEGRADED, 'Tableau server degraded'),

            (CustomAlerts.BACKUP_STARTED, 'Backup Started'),
            (CustomAlerts.BACKUP_FINISHED, 'Backup Finished'),
            (CustomAlerts.BACKUP_FAILED, 'Backup Failed'),

            (CustomAlerts.RESTORE_STARTED, 'Restore Started'),
            (CustomAlerts.RESTORE_FINISHED, 'Restore Finished'),
            (CustomAlerts.RESTORE_FAILED, 'Restore Failed'),

            (CustomAlerts.TABLEAU_START_FAILED, 'Tableau Start Failed'),

            (CustomAlerts.MAINT_START_FAILED,
                                'Could not start Maintenance Web Server'),
            (CustomAlerts.MAINT_STOP_FAILED,
                                'Could not stop Maintenance Web Server'),

            (CustomAlerts.MAINT_OFFLINE, 'Maintenance web page is now offline'),
            (CustomAlerts.MAINT_ONLINE, 'Maintenance web page is now online'),

            (CustomAlerts.ARCHIVE_START_FAILED,
                                        'Could not start Archive Web Server'),
            (CustomAlerts.ARCHIVE_STOP_FAILED,
                                        'Could not stop Archive Web Server'),

            (CustomAlerts.AGENT_COMM_LOST, 'Communication lost with agent'),
            (CustomAlerts.AGENT_FAILED_STATUS, 'Failed status from agent'),
            (CustomAlerts.AGENT_RETURNED_INVALID_STATUS,
                                        'Agent returned invalid status')
        ]
        entry = meta.Session.query(CustomAlertsEntry).first()

        if entry:
            return

        for alert in entries:
            entry = apply(CustomAlertsEntry, alert)
            meta.Session.add(entry)

        meta.Session.commit()
