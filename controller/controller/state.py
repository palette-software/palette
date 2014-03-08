import sqlalchemy
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, func
from sqlalchemy.schema import ForeignKey, UniqueConstraint
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
import platform

import meta

from alert import Alert

# The tabadmin state table:
#   main   state: starting, started, stopping, stopped, unknown
#   backup state: backup, restore or none

class StateEntry(meta.Base):
    __tablename__ = 'state'

    # State types
    STATE_TYPE_MAIN="main"
    STATE_TYPE_BACKUP="backup"

    # main states
    STATE_MAIN_STARTING="starting"
    STATE_MAIN_STARTED="started"
    STATE_MAIN_STOPPING="stopping"
    STATE_MAIN_STOPPED="stopped"
    STATE_MAIN_UNKNOWN="unknown"

    # backup states
    STATE_BACKUP_BACKUP="backup"
    STATE_BACKUP_RESTORE="restore"
    STATE_BACKUP_NONE="none"

    # FIXME: Make combination of domainid and state_type a unique key

    state_type = Column(String, unique=True, nullable=False, primary_key=True)
    domainid = Column(BigInteger, ForeignKey("domain.domainid"), nullable=False)
    state = Column(String)
    creation_time = Column(DateTime, server_default=func.now())
    modification_time = Column(DateTime, server_default=func.now(), \
      server_onupdate=func.current_timestamp())
    UniqueConstraint('domainid', 'state_type')

    def __init__(self, domainid, state_type, state):
        self.domainid = domainid
        self.state_type = state_type
        self.state = state

class StateManager(object):

    def __init__(self, server):
        self.server = server
        self.config = self.server.config
        self.log = self.server.log
        self.Session = sessionmaker(bind=meta.engine)
        self.domainid = self.server.domainid

    def update(self, state_type, state):
        session = self.Session()
        entry = session.query(StateEntry).\
            filter(StateEntry.domainid == self.domainid).\
            filter(StateEntry.state_type == state_type).first()

        if entry:
            session.query(StateEntry).\
                filter(StateEntry.domainid == self.domainid).\
                filter(StateEntry.state_type == state_type).\
                update({'state': state})

        else:
            entry = StateEntry(self.domainid, state_type, state)
            session.add(entry)

        session.commit()
        session.close()

        # Send out the main started/stopped alert.
        # Backup alerts (backup/restore started/stopped done elsewhere).
        if state_type == StateEntry.STATE_TYPE_MAIN and state in \
          [StateEntry.STATE_MAIN_STARTED, StateEntry.STATE_MAIN_STOPPED]:
            alert = Alert(self.config, self.log)
            alert.send("Tableau server " + state)

    def get_states(self):
        session = self.Session()
        try:
            main_entry = session.query(StateEntry).\
                filter(StateEntry.domainid == self.domainid).\
                filter(StateEntry.state_type == StateEntry.STATE_TYPE_MAIN).\
                one()
            main_status = main_entry.state
        except NoResultFound, e:
            main_status = StateEntry.STATE_MAIN_UNKNOWN
        except Exception, e:
            session.close()
            raise e

        try:
            backup_entry = session.query(StateEntry).\
                filter(StateEntry.domainid == self.domainid).\
                filter(StateEntry.state_type == StateEntry.STATE_TYPE_BACKUP).\
                one()
            backup_status = backup_entry.state
        except NoResultFound, e:
            backup_status = StateEntry.STATE_BACKUP_NONE
        except Exception, e:
            session.close()
            raise e

        session.close()
        return { StateEntry.STATE_TYPE_MAIN: main_status, \
          StateEntry.STATE_TYPE_BACKUP: backup_status }
