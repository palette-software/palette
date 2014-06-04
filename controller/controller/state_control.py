from sqlalchemy import Column, BigInteger, String
from sqlalchemy.orm.exc import NoResultFound

from akiri.framework.ext.sqlalchemy import meta

from state import StateManager
from mixin import BaseMixin

class StateControl(meta.Base, BaseMixin):
    __tablename__ = "state_control"

    stateid = Column(BigInteger, unique=True, nullable=False, \
                                   autoincrement=True, primary_key=True)

    state = Column(String, unique=True)
    text = Column(String)
    allowable_actions = Column(String)
    color = Column(String)  # icon color: e.g. red, green, yellow

    # Allowable actions:
    ACTION_START="start"
    ACTION_STOP="stop"
    ACTION_BACKUP="backup"
    ACTION_RESTORE="restore"
    ACTION_RESET="reset"
    ACTION_RESTART="restart"
    ACTION_NONE=""

    COLOR_RED="red"
    COLOR_GREEN="green"
    COLOR_YELLOW="yellow"

    @classmethod
    def get_state_control_entry(cls, state):

        try:
            entry = meta.Session.query(StateControl).\
                filter(StateControl.state == state).one()
        except NoResultFound, e:
            return None

        return entry

    # fixme: Populate the table elsewhere.
    defaults = [
        {'state': StateManager.STATE_DISCONNECTED,
            'text': "Disconnected from the primary agent",
            'allowable_actions': ACTION_NONE,
            'color': COLOR_RED},

        # connected but no status reported from tabadmin yet
        {'state': StateManager.STATE_PENDING,
            'text': "Primary agent is connected.  Retrieving Tableau status.",
            'allowable_actions': ACTION_NONE,
            'color': COLOR_YELLOW},

        {'state': StateManager.STATE_STOPPING,
            'text': "Tableau is stopping",
            'allowable_actions': ACTION_NONE,
            'color': COLOR_YELLOW},

        {'state': StateManager.STATE_STOPPING_RESTORE,
            'text': "Stopping Tableau in preparation to start a restore.",
            'allowable_actions': ACTION_NONE,
            'color': COLOR_YELLOW},

        {'state': StateManager.STATE_STOPPED,
            'text': "Tableau is stopped.",
            'allowable_actions': ' '.join([ACTION_START, 
                        ACTION_BACKUP,
                        ACTION_RESTORE,
                        ACTION_RESET,
                        ACTION_RESTART]),
            'color': COLOR_RED},

        # reported from tabadmin
        {'state': StateManager.STATE_STOPPED_RESTORE,
            'text': "Performing a restore.  Tableau is stopped.",
            'allowable_actions': ACTION_NONE,
            'color': COLOR_GREEN},

        {'state': StateManager.STATE_STOPPED_BACKUP,
            'text': "Performing a backup.  Tableau is stopped.",
            'allowable_actions': ACTION_NONE,
            'color': COLOR_GREEN},

        # backup for/before restore
        {'state': StateManager.STATE_STOPPED_BACKUP_RESTORE,
            'text':
                "Performing a backup before a restore.  Tableau is stopped.",
            'allowable_actions': ACTION_NONE,
            'color': COLOR_GREEN},

        {'state': StateManager.STATE_STOPPED_BACKUPDEL,
            'text': "Deleting a backup.  Tableau is stopped.",
            'allowable_actions': ACTION_NONE,
            'color': COLOR_RED},

        {'state': StateManager.STATE_STOPPED_ZIPLOGS,
            'text': "Running ziplogs.  Tableau is stopped.",
            'allowable_actions': ACTION_NONE,
            'color': COLOR_RED},

        {'state': StateManager.STATE_STARTING,
            'text': "Starting Tableau.",
            'allowable_actions': ACTION_NONE,
            'color': COLOR_YELLOW},

        {'state': StateManager.STATE_STARTING_RESTORE,
            'text': "Starting a restore.",
            'allowable_actions': ACTION_NONE,
            'color': COLOR_GREEN},

        {'state': StateManager.STATE_STARTED,
            'text': "Tableau is running.",
            'allowable_actions': ' '.join([ACTION_STOP, 
                        ACTION_BACKUP,
                        ACTION_RESTORE,
                        ACTION_RESET,
                        ACTION_RESTART]),
            'color': COLOR_GREEN},

        {'state': StateManager.STATE_STARTED_BACKUP,
            'text': "Performing a backup.  Tableau is running.",
            'allowable_actions': ACTION_NONE,
            'color': COLOR_GREEN},

        # backup for/before restore
        {'state': StateManager.STATE_STARTED_BACKUP_RESTORE,
            'text': "Performing a backup before a restore is done. " + \
            "Tableau is running.",
            'allowable_actions': ACTION_NONE,
            'color': COLOR_GREEN},

        # backup for/before stop
        {'state': StateManager.STATE_STARTED_BACKUP_STOP,
            'text': "Performing a backup before Tableau is stopped.",
            'allowable_actions': ACTION_NONE,
            'color': COLOR_GREEN},

        {'state': StateManager.STATE_STARTED_BACKUPDEL,
            'text': "Deleting a backup.  Tableau is running.",
            'allowable_actions': ACTION_NONE,
            'color': COLOR_GREEN},

        {'state': StateManager.STATE_STARTED_ZIPLOGS,
            'text': "Running ziplogs.  Tableau is running.",
            'allowable_actions': ACTION_NONE,
            'color': COLOR_GREEN},

        {'state': StateManager.STATE_DEGRADED,
            'text': "Tableau is in a DEGRADED state.",
            'allowable_actions': ACTION_STOP,
            'color': COLOR_RED},

        {'state': StateManager.STATE_UNKNOWN,
            'text': "No primary agent has connected to this controller.",
            'allowable_actions': ACTION_NONE,
            'color': COLOR_RED}
    ]
