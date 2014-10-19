from sqlalchemy import Column, BigInteger, String
from sqlalchemy.orm.exc import NoResultFound

# pylint: disable=import-error,no-name-in-module
from akiri.framework.ext.sqlalchemy import meta
# pylint: enable=import-error,no-name-in-module

from mixin import BaseMixin

class StateControl(meta.Base, BaseMixin):
    __tablename__ = "state_control"

    stateid = Column(BigInteger, unique=True, nullable=False,
                                   autoincrement=True, primary_key=True)

    state = Column(String, unique=True)
    text = Column(String)
    allowable_actions = Column(String)
    icon = Column(String)
    color = Column(String)  # icon color: e.g. red, green, yellow

    # Allowable actions:
    ACTION_START = "start"
    ACTION_STOP = "stop"
    ACTION_BACKUP = "backup"
    ACTION_RESTORE = "restore"
    ACTION_RESET = "reset"
    ACTION_RESTART = "restart"
    ACTION_NONE = ""

    COLOR_RED = "red"
    COLOR_GREEN = "green"
    COLOR_YELLOW = "yellow"

    @classmethod
    def get_state_control_entry(cls, state):

        try:
            entry = meta.Session.query(StateControl).\
                filter(StateControl.state == state).one()
        except NoResultFound:
            return None

        return entry

    defaults_filename = 'state_control.json'
