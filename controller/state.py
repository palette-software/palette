import sqlalchemy
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.schema import ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

import meta

# The tabadmin state: starting, started, stopping, stopped

class StateEntry(meta.Base):
    __tablename__ = 'state'

    state = Column(String, primary_key=True)
    creation_time = Column(DateTime, default=func.now())

    def __init__(self, state):
        self.state = state

class StateManager(object):

    def __init__(self):
    
        url = "postgresql://palette:palpass@localhost/paldb"
        self.engine = sqlalchemy.create_engine(url, echo=False)

        meta.Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def update(self, state):
        self.session.query(StateEntry).\
            delete()

        entry = StateEntry(state)
        self.session.add(entry)
        self.session.commit()
