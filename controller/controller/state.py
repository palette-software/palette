import sqlalchemy
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, func
from sqlalchemy.schema import ForeignKey, UniqueConstraint
from sqlalchemy.orm.exc import NoResultFound
import platform

from custom_alerts import CustomAlerts

import meta

from alert import Alert

class StateEntry(meta.Base):
    __tablename__ = 'state'

    # possible states
    STATE_DISCONNECTED="DISCONNECTED"
    # connected but no status reported from tabadmin yet
    STATE_PENDING="PENDING"

    STATE_STOPPING="STOPPING"
    STATE_STOPPING_RESTORE="STOPPING-RESTORE"

    STATE_STOPPED="STOPPED"         # reported from tabadmin
    STATE_STOPPED_RESTORE="STOPPED-RESTORE"
    STATE_STOPPED_BACKUP="STOPPED-BACKUP"
    # backup for/before restore
    STATE_STOPPED_BACKUP_RESTORE="STOPPED-BACKUP-RESTORE"

    STATE_STARTING="STARTING"
    STATE_STARTING_RESTORE="STARTING-RESTORE"

    STATE_STARTED="STARTED"         # reported as "running" from tabadmin
    STATE_STARTED_BACKUP="STARTED-BACKUP"
    # backup for/before restore
    STATE_STARTED_BACKUP_RESTORE="STARTED-BACKUP-RESTORE"
    # backup for/before stop
    STATE_STARTED_BACKUP_STOP="STARTED-BACKUP-STOP"

    STATE_DEGRADED="DEGRADED"       # reported from tabadmin

    STATE_UNKNOWN="UNKNOWN"        # no primary ever connected to the controller

    # Allowable actions:
    ACTION_START="start"
    ACTION_STOP="stop"
    ACTION_RESET="reset"
    ACTION_RESTART="restart"

    domainid = Column(BigInteger, ForeignKey("domain.domainid"),
                                        nullable=False, primary_key=True)
    state = Column(String)
    allowable_actions = Column(String)
    creation_time = Column(DateTime, server_default=func.now())
    modification_time = Column(DateTime, server_default=func.now(), \
      server_onupdate=func.current_timestamp())

class StateManager(object):

    def __init__(self, server):
        self.server = server
        self.config = self.server.config
        self.log = self.server.log
        self.domainid = self.server.domainid

    def update(self, state):
        if state == "RUNNING":
            # tabadmin calls it "RUNNING", we called it "STARTED"
            state = StateEntry.STATE_STARTED

        # Determine what allowable actions are for the given state
        # (Only for stop/start/reset/restart and not backup/restore-related)
        if state == StateEntry.STATE_STARTED:
            allowable_actions = ' '.join(\
                [StateEntry.ACTION_STOP, StateEntry.ACTION_RESET,
                                                        StateEntry.ACTION_RESTART])
        elif state == StateEntry.STATE_STOPPED:
            allowable_actions = ' '.join(
                [StateEntry.ACTION_START, StateEntry.ACTION_RESET,
                                                        StateEntry.ACTION_RESTART])
        else:
            allowable_actions = ""

        self.log.info("-------state changing to %s----------", state)
        session = meta.Session()
        entry = session.query(StateEntry).\
            filter(StateEntry.domainid == self.domainid).first()

        if entry:
            session.query(StateEntry).\
                filter(StateEntry.domainid == self.domainid).\
                update({'state': state,
                        'allowable_actions': allowable_actions})
        else:
            entry = StateEntry(domainid=self.domainid, state=state)
            session.add(entry)

        session.commit()

    def get_state(self):
        return StateManager.get_state_by_domainid(self.domainid)

    @classmethod
    def get_state_by_domainid(cls, domainid):
        try:
            main_entry = meta.Session.query(StateEntry).\
                filter(StateEntry.domainid == domainid).\
                one()
            main_status = main_entry.state
        except NoResultFound, e:
            main_status = StateEntry.STATE_UNKNOWN

        return main_status
