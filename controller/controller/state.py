from manager import Manager
from system import SystemEntry, SystemManager

class StateManager(Manager):
    # possible states
    STATE_DISCONNECTED = "DISCONNECTED"
    # connected but no status reported from tabadmin yet
    STATE_PENDING = "PENDING"

    STATE_STOPPING = "STOPPING"
    STATE_STOPPING_RESTORE = "STOPPING-RESTORE"

    STATE_STOPPED = "STOPPED"     # reported from tabadmin

    # The user stopped tableau outside of palette
    STATE_STOPPED_UNEXPECTED = "STOPPED-UNEXPECTED"

    STATE_STOPPED_RESTORE = "STOPPED-RESTORE"
    STATE_STOPPED_BACKUP = "STOPPED-BACKUP"
    # backup for/before restore
    STATE_STOPPED_BACKUP_RESTORE = "STOPPED-BACKUP-RESTORE"

    STATE_STOPPED_FILEDEL = "STOPPED-FILEDEL"
    STATE_STOPPED_ZIPLOGS = "STOPPED-ZIPLOGS"

    STATE_STARTING = "STARTING"
    STATE_STARTING_RESTORE = "STARTING-RESTORE"

    STATE_STARTED = "STARTED"         # reported as "running" from tabadmin
    STATE_STARTED_BACKUP = "STARTED-BACKUP"
    # backup for/before restore
    STATE_STARTED_BACKUP_RESTORE = "STARTED-BACKUP-RESTORE"
    # backup for/before stop
    STATE_STARTED_BACKUP_STOP = "STARTED-BACKUP-STOP"
    # backup for/before restart
    STATE_STARTED_BACKUP_RESTART = "STARTED-BACKUP-RESTART"
    STATE_RESTARTING = "RESTARTING"

    STATE_STARTED_FILEDEL = "STARTED-FILEDEL"
    STATE_STARTED_ZIPLOGS = "STARTED-ZIPLOGS"

    STATE_STARTED_CLEANUP = "STARTED-CLEANUP"
    STATE_STOPPED_CLEANUP = "STOPPED-CLEANUP"

    STATE_DEGRADED = "DEGRADED"   # reported from tabadmin

    STATE_UPGRADING = "UPGRADING" # agent or controller is upgrading

    STATE_UNKNOWN = "UNKNOWN"     # no primary ever connected to the controller

    def __init__(self, server):
        super(StateManager, self).__init__(server)
        self.system = self.server.system
        self.config = self.server.config
        self.log = self.server.log

    def update(self, state):
        if state == "RUNNING":
            # tabadmin calls it "RUNNING"; we called it "STARTED"
            state = StateManager.STATE_STARTED

        self.log.info("-------state changing to %s----------", state)

        self.system.save(SystemManager.SYSTEM_KEY_STATE, state)

    def get_state(self):
        return StateManager.get_state_by_envid(self.envid)

    @classmethod
    def get_state_by_envid(cls, envid):
        entry = SystemEntry.get_by_key(envid, SystemManager.SYSTEM_KEY_STATE)
        return entry and entry.value or StateManager.STATE_DISCONNECTED
