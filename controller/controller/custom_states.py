import sqlalchemy
from sqlalchemy import Column, BigInteger, String
from sqlalchemy.orm.exc import NoResultFound
import meta

from state import StateEntry

class CustomStatesEntry(meta.Base):
    __tablename__ = "custom_states"

    stateid = Column(BigInteger, unique=True, nullable=False, \
                                   autoincrement=True, primary_key=True)

    state = Column(String, unique=True)
    text = Column(String)
    color = Column(String)  # icon color: e.g. red, green, yellow

    def __init__(self, state, text, color):
        self.state = state
        self.text = text
        self.color = color

class CustomStates(object):

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
            (StateEntry.STATE_DISCONNECTED,
                "Disconnected from the primary agent",
                "red"),

            # connected but no status reported from tabadmin yet
            (StateEntry.STATE_PENDING,
                "Primary agent is connected.  Retrieving Tableau status.",
                "yellow"),

            (StateEntry.STATE_STOPPING,
                "Tableau is stopping",
                "yellow"),

            (StateEntry.STATE_STOPPING_RESTORE,
                "Stopping Tableau in preparation to start a restore.",
                "yellow"),

            (StateEntry.STATE_STOPPED,
                "Tableau is stopped.",
                "red"),

            # reported from tabadmin
            (StateEntry.STATE_STOPPED_RESTORE,
                "Performing a restore.  Tableau is stopped.",
                "green"),

            (StateEntry.STATE_STOPPED_BACKUP,
                "Performing a backup.  Tableau is stopped.",
                "green"),

            # backup for/before restore
            (StateEntry.STATE_STOPPED_BACKUP_RESTORE,
                "Performing a backup before a restore.  Tableau is stopped.",
                "green"),

            (StateEntry.STATE_STARTING,
                "Starting Tableau.",
                "yellow"),

            (StateEntry.STATE_STARTING_RESTORE,
                "Starting a restore.",
                "green"),

            (StateEntry.STATE_STARTED,
                "Tableau is running.",
                "green"),

            (StateEntry.STATE_STARTED_BACKUP,
                "Performing a backup.  Tableau is running.",
                "green"),

            # backup for/before restore
            (StateEntry.STATE_STARTED_BACKUP_RESTORE,
                "Performing a backup before a restore is done. " + \
                "Tableau is running.",
                "green"),

            # backup for/before stop
            (StateEntry.STATE_STARTED_BACKUP_STOP,
                "Performing a backup before Tableau is stopped.",
                "green"),

            (StateEntry.STATE_DEGRADED,
                "Tableau is in a DEGRADED state.",
                "red"),

            (StateEntry.STATE_UNKNOWN,
                "No primary agent has connected to this controller.",
                "red")
        ]

        entry = meta.Session.query(CustomStatesEntry).first()

        if entry:
            return

        for state in entries:
            entry = apply(CustomStatesEntry, state)
            meta.Session.add(entry)

        meta.Session.commit()
