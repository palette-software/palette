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

    # level: E (Error), W (Warning) or I (Info)
    level = Column(String(1))

    # subject is a python key-value substitution template for the subject
    subject = Column(String) # The custom message for the 'key'.

    # message is a mako template for the message
    message = Column(String)

    icon = Column(String)
    color = Column(String)

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

    # levels
    LEVEL_ERROR="E"
    LEVEL_WARNING="W"
    LEVEL_INFO="I"

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
                        CustomAlerts.LEVEL_INFO,
                        'Controller started.  Initial tableau state: running'),
            (CustomAlerts.INIT_STATE_STOPPED,
                        CustomAlerts.LEVEL_INFO,
                        'Controller started.  Initial tableau state: stopped'),
            (CustomAlerts.INIT_STATE_DEGRADED,
                        CustomAlerts.LEVEL_INFO,
                        'Controller started.  Initial tableau state: degraded'),

            (CustomAlerts.STATE_STARTED,
                            CustomAlerts.LEVEL_INFO,
                            'Tableau server running'),
            (CustomAlerts.STATE_STOPPED,
                            CustomAlerts.LEVEL_INFO,
                            'Tableau server stopped'),
            (CustomAlerts.STATE_DEGRADED,
                            CustomAlerts.LEVEL_INFO,
                            'Tableau server degraded'),

            (CustomAlerts.BACKUP_STARTED,
                            CustomAlerts.LEVEL_INFO,
                            'Backup Started'),
            (CustomAlerts.BACKUP_FINISHED,
                            CustomAlerts.LEVEL_INFO,
                            'Backup Finished'),
            (CustomAlerts.BACKUP_FAILED,
                            CustomAlerts.LEVEL_INFO,
                            'Backup Failed'),

            (CustomAlerts.BACKUP_BEFORE_RESTORE_STARTED,
                                    CustomAlerts.LEVEL_INFO,
                                    'Backup Before Restore Started'),
            (CustomAlerts.BACKUP_BEFORE_RESTORE_FINISHED,
                                    CustomAlerts.LEVEL_INFO,
                                    'Backup Before Restore Finished'),
            (CustomAlerts.BACKUP_BEFORE_RESTORE_FAILED,
                                    CustomAlerts.LEVEL_ERROR,
                                    'Backup Before Restore Failed'),

            (CustomAlerts.RESTORE_STARTED,
                                    CustomAlerts.LEVEL_INFO,
                                    'Restore Started'),
            (CustomAlerts.RESTORE_FINISHED,
                                    CustomAlerts.LEVEL_INFO,
                                    'Restore Finished'),
            (CustomAlerts.RESTORE_FAILED,
                                    CustomAlerts.LEVEL_ERROR,
                                    'Restore Failed'),

            (CustomAlerts.TABLEAU_START_FAILED,
                                    CustomAlerts.LEVEL_ERROR,
                                    'Tableau Start Failed'),

            (CustomAlerts.MAINT_START_FAILED,
                                    CustomAlerts.LEVEL_ERROR,
                                    'Could not start Maintenance Web Server'),
            (CustomAlerts.MAINT_STOP_FAILED,
                                    CustomAlerts.LEVEL_ERROR,
                                    'Could not stop Maintenance Web Server'),

            (CustomAlerts.MAINT_OFFLINE,
                                    CustomAlerts.LEVEL_INFO,
                                    'Maintenance web page is now offline'),
            (CustomAlerts.MAINT_ONLINE,
                                    CustomAlerts.LEVEL_INFO,
                                    'Maintenance web page is now online'),

            (CustomAlerts.ARCHIVE_START_FAILED,
                                    CustomAlerts.LEVEL_ERROR,
                                    'Could not start Archive Web Server'),
            (CustomAlerts.ARCHIVE_STOP_FAILED,
                                    CustomAlerts.LEVEL_ERROR,
                                    'Could not stop Archive Web Server'),

            (CustomAlerts.AGENT_COMM_LOST,
                                    CustomAlerts.LEVEL_ERROR,
                                    'Communication lost with agent'),
            (CustomAlerts.AGENT_FAILED_STATUS,
                                    CustomAlerts.LEVEL_ERROR,
                                    'Failed status from agent'),
            (CustomAlerts.AGENT_RETURNED_INVALID_STATUS,
                                    CustomAlerts.LEVEL_ERROR,
                                    'Agent returned invalid status')
        ]
        entry = meta.Session.query(CustomAlertsEntry).first()

        if entry:
            return

        for alert in entries:
            entry = CustomAlertsEntry()
            entry.key = alert[0]
            entry.level = alert[1]
            entry.subject = alert[2]
            meta.Session.add(entry)

        meta.Session.commit()
