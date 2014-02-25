import sqlalchemy
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, func
from sqlalchemy.schema import ForeignKey, UniqueConstraint
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
import platform

import meta

from inits import *
from alert import Alert

# The tabadmin state table:
#   main   state: starting, started, stopping, stopped, unknown
#   second state: backup, restore or none

class StateEntry(meta.Base):
    __tablename__ = 'state'

    # FIXME: Make combination of agentid and state_type a unique key

    state_type = Column(String, unique=True, nullable=False, primary_key=True)
    agentid = Column(BigInteger, ForeignKey("agents.agentid"))
    state = Column(String)
    creation_time = Column(DateTime, server_default=func.now(), \
      onupdate=func.current_timestamp())
    UniqueConstraint('agentid', 'state_type')

    # FIXME: In theory we want agentid here, but many places that call this
    #        method do not have agentid available. Consider using domainid
    #        rather than agentid for state.
    def __init__(self, state_type, state):
        self.state_type = state_type
        self.state = state

class StateManager(object):

    def __init__(self, config, log):
        self.config = config
        self.log = log
        self.Session = sessionmaker(bind=meta.engine)

    def update(self, state_type, state):
        session = self.Session()
        entry = session.query(StateEntry).\
            filter(StateEntry.state_type == state_type).first()

        if entry:
            session.query(StateEntry).\
            filter(StateEntry.state_type == state_type).\
                update({'state': state})

        else:
            entry = StateEntry(state_type, state)
            session.add(entry)

        session.commit()
        session.close()

        # Send out the main started stopped alert.
        # Second alerts (backup/restore started/stopped done elsewhere).
        if state_type == STATE_TYPE_MAIN and state in [STATE_MAIN_STARTED, STATE_MAIN_STOPPED]:
            alert = Alert(self.config, self.log)
            alert.send("Tableau server " + state)

    def get_states(self):
        session = self.Session()
        try:
            main_entry = session.query(StateEntry).\
                filter(StateEntry.state_type == STATE_TYPE_MAIN).one()
            main_status = main_entry.state
        except NoResultFound, e:
            main_status = STATE_MAIN_UNKNOWN

        try:
            second_entry = session.query(StateEntry).\
                filter(StateEntry.state_type == STATE_TYPE_SECOND).one()
            second_status = second_entry.state

        except NoResultFound, e:
            second_status = STATE_SECOND_NONE

        session.close()
        return { STATE_TYPE_MAIN: main_status, STATE_TYPE_SECOND: second_status }
