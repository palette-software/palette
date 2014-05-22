from sqlalchemy import Column, BigInteger, String
from sqlalchemy.orm.exc import NoResultFound

from akiri.framework.ext.sqlalchemy import meta

from state import StateManager

class CustomStatesEntry(meta.Base):
    __tablename__ = "custom_states"

    stateid = Column(BigInteger, unique=True, nullable=False, \
                                   autoincrement=True, primary_key=True)

    state = Column(String, unique=True)
    text = Column(String)
    allowable_actions = Column(String)
    color = Column(String)  # icon color: e.g. red, green, yellow

class CustomStates(object):

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
    def get_custom_state_entry(cls, state):

        try:
            entry = meta.Session.query(CustomStatesEntry).\
                filter(CustomStatesEntry.state == state).one()
        except NoResultFound, e:
            return None

        return entry

    def populate(self):
        """Populate the initial custom states table if it is empty."""

        # fixme: Init the custom states elsewhere.
        entries = [
            (StateManager.STATE_DISCONNECTED,
                "Disconnected from the primary agent",
                CustomStates.ACTION_NONE,
                CustomStates.COLOR_RED),

            # connected but no status reported from tabadmin yet
            (StateManager.STATE_PENDING,
                "Primary agent is connected.  Retrieving Tableau status.",
                CustomStates.ACTION_NONE,
                CustomStates.COLOR_YELLOW),

            (StateManager.STATE_STOPPING,
                "Tableau is stopping",
                CustomStates.ACTION_NONE,
                CustomStates.COLOR_YELLOW),

            (StateManager.STATE_STOPPING_RESTORE,
                "Stopping Tableau in preparation to start a restore.",
                CustomStates.ACTION_NONE,
                CustomStates.COLOR_YELLOW),

            (StateManager.STATE_STOPPED,
                "Tableau is stopped.",
                ' '.join([CustomStates.ACTION_START, 
                            CustomStates.ACTION_BACKUP,
                            CustomStates.ACTION_RESTORE,
                            CustomStates.ACTION_RESET,
                            CustomStates.ACTION_RESTART]),
                CustomStates.COLOR_RED),

            # reported from tabadmin
            (StateManager.STATE_STOPPED_RESTORE,
                "Performing a restore.  Tableau is stopped.",
                CustomStates.ACTION_NONE,
                CustomStates.COLOR_GREEN),

            (StateManager.STATE_STOPPED_BACKUP,
                "Performing a backup.  Tableau is stopped.",
                CustomStates.ACTION_NONE,
                CustomStates.COLOR_GREEN),

            # backup for/before restore
            (StateManager.STATE_STOPPED_BACKUP_RESTORE,
                "Performing a backup before a restore.  Tableau is stopped.",
                CustomStates.ACTION_NONE,
                CustomStates.COLOR_GREEN),

            (StateManager.STATE_STARTING,
                "Starting Tableau.",
                CustomStates.ACTION_NONE,
                CustomStates.COLOR_YELLOW),

            (StateManager.STATE_STARTING_RESTORE,
                "Starting a restore.",
                CustomStates.ACTION_NONE,
                CustomStates.COLOR_GREEN),

            (StateManager.STATE_STARTED,
                "Tableau is running.",
                ' '.join([CustomStates.ACTION_STOP, 
                            CustomStates.ACTION_BACKUP,
                            CustomStates.ACTION_RESTORE,
                            CustomStates.ACTION_RESET,
                            CustomStates.ACTION_RESTART]),
                CustomStates.COLOR_GREEN),

            (StateManager.STATE_STARTED_BACKUP,
                "Performing a backup.  Tableau is running.",
                CustomStates.ACTION_NONE,
                CustomStates.COLOR_GREEN),

            # backup for/before restore
            (StateManager.STATE_STARTED_BACKUP_RESTORE,
                "Performing a backup before a restore is done. " + \
                "Tableau is running.",
                CustomStates.ACTION_NONE,
                CustomStates.COLOR_GREEN),

            # backup for/before stop
            (StateManager.STATE_STARTED_BACKUP_STOP,
                "Performing a backup before Tableau is stopped.",
                CustomStates.ACTION_NONE,
                CustomStates.COLOR_GREEN),

            (StateManager.STATE_DEGRADED,
                "Tableau is in a DEGRADED state.",
                CustomStates.ACTION_STOP,
                CustomStates.COLOR_RED),

            (StateManager.STATE_UNKNOWN,
                "No primary agent has connected to this controller.",
                CustomStates.ACTION_NONE,
                CustomStates.COLOR_RED)
        ]

        entry = meta.Session.query(CustomStatesEntry).first()

        if entry:
            return

        for state in entries:
            entry = apply(CustomStatesEntry)
            entry.state = state[0]
            entry.text = state[1]
            entry.allowable_actions = state[2]
            entry.color = state[3]
            meta.Session.add(entry)

        meta.Session.commit()
