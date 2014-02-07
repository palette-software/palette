import sqlalchemy
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.schema import ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

import meta

from inits import *

# The tabadmin state table:
#   main   state: starting, started, stopping, stopped, unknown
#   second state: backup, restore or none

class StateEntry(meta.Base):
    __tablename__ = 'state'

    state_type = Column(String, primary_key=True)
    state = Column(String)
    creation_time = Column(DateTime, server_default=func.now(), onupdate=func.current_timestamp())

    def __init__(self, state_type, state):
        self.state_type = state_type
        self.state = state

class StateManager(object):

    def __init__(self):
    
        url = "postgresql://palette:palpass@localhost/paldb"
        self.engine = sqlalchemy.create_engine(url, echo=False)

        meta.Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def update(self, state_type, state):
        entry = self.session.query(StateEntry).\
            filter(StateEntry.state_type == state_type).first()

        if entry:
            self.session.query(StateEntry).\
            filter(StateEntry.state_type == state_type).\
                update({'state': state})

        else:
            entry = StateEntry(state_type, state)
            self.session.add(entry)

        self.session.commit()

    def get_states(self):
        try:
            main_entry = self.session.query(StateEntry).\
                filter(StateEntry.state_type == STATE_TYPE_MAIN).one()
            main_status = main_entry.state
        except NoResultFound, e:
            main_status = STATE_MAIN_UNKNOWN

        try:
            second_entry = self.session.query(StateEntry).\
                filter(StateEntry.state_type == STATE_TYPE_SECOND).one()
            second_status = second_entry.state

        except NoResultFound, e:
            second_status = STATE_SECOND_NONE

        return { STATE_TYPE_MAIN: main_status, STATE_TYPE_SECOND: second_status }
