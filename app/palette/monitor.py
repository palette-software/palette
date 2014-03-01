import sqlalchemy
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, func
from sqlalchemy.orm.exc import NoResultFound
import meta
import sys

from akiri.framework.api import RESTApplication, DialogPage
from akiri.framework.config import store

from controller.backup import BackupEntry
from controller.agentstatus import AgentStatusEntry

from . import Session

__all__ = ["MonitorApplication"]

# State types:
STATE_TYPE_MAIN="main"
STATE_TYPE_SECOND="second"

class MonitorApplication(RESTApplication):

    NAME = 'monitor'

    def __init__(self, global_conf):
        super(MonitorApplication, self).__init__(global_conf)

        self.domainname = store.get('palette', 'domainname')

    def handle(self, req):
        db_session = Session()

        tableau_status = "Unknown"
        main_state = "Not connected"
        secondary_state = "none"

        try:
            primary_agents = db_session.query(AgentStatusEntry).\
                filter(AgentStatusEntry.agent_type == "primary").all()
        except NoResultFound, e:
            primary_agents = None

        # If there is more than one primary agent in the table, look for
        # the primary agent that is connected and use that.
        # the table.

        primary = None

        if primary_agents:
            for agent in primary_agents:
                if agent.last_disconnect_time:
                    if agent.last_disconnect_time > agent.last_connection_time:
                        # This agent has disconnected.
                        continue
                    else:
                        # This primary agent is connected.  We will use it.
                        primary = agent
                        break
                else:
                    primary = agent
                    break

        # If there is a primary agent connected, get tableau status,
        # main, and secondary states.
        if primary:
            # Dig out the tableau status.
            try:
                tableau_entry = db_session.query(StatusEntry).\
                    filter(StatusEntry.name == 'Status').one()
                tableau_status = tableau_entry.status
            except NoResultFound, e:
                pass

            # Dig out the states
            state_entries = db_session.query(StateEntry).all()

            for state_entry in state_entries:
                if state_entry.state_type == STATE_TYPE_MAIN:
                    main_state = state_entry.state
                elif state_entry.state_type == STATE_TYPE_SECOND:
                    secondary_state = state_entry.state
                else:
                    print "monitor: Uknown state_type:", state_entry.state_type

        # Dig out the last/most recent backup.
        last_db = db_session.query(BackupEntry).\
                order_by(BackupEntry.creation_time.desc()).\
                first()

        if last_db:
            last_backup = str(last_db.creation_time)[:19]
        else:
            last_backup = "none"

        db_session.close()

#        print 'tableau-status: %s, main-state: %s, secondary-state: %s, last-backup: %s' % (tableau_status, main_state, secondary_state, last_backup)

        return {'tableau-status': tableau_status,
                'main-state': main_state,
                'secondary-state': secondary_state,
                'last-backup': last_backup
                }

class StateEntry(meta.Base):
    __tablename__ = 'state'

    state_type = Column(String, primary_key=True)
    state = Column(String)
    creation_time = Column(DateTime, server_default=func.now(), onupdate=func.current_timestamp())

    def __init__(self, state_type, state):
        self.state_type = state_type
        self.state = state

class StatusEntry(meta.Base):
    __tablename__ = 'status'

    name = Column(String, primary_key=True)
    pid = Column(Integer)
    status = Column(String)
    creation_time = Column(DateTime, default=func.now())

    def __init__(self, name, pid, status):
        self.name = name
        self.pid = pid
        self.status = status

class StatusDialog(DialogPage):

    NAME = "status"
    TEMPLATE = "status.mako"

    def __init__(self, global_conf):
        super(StatusDialog, self).__init__(global_conf)

        self.domainname = store.get('palette', 'domainname')

        db_session = Session()
        self.status_entries = db_session.query(StatusEntry).all()

        # Dig out the main status and time
        self.main_status = "Unknown"
        self.status_time = "Unknown"
        for entry in self.status_entries:
            if entry.name == 'Status':
                self.main_status = entry.status
                self.status_time = str(entry.creation_time)[:19] # Cut off fraction
        db_session.close()
