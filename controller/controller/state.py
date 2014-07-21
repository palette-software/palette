import platform
from system import SystemManager

class StateManager(object):
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
    STATE_STOPPED_BACKUPDEL="STOPPED-BACKUPDEL"
    STATE_STOPPED_ZIPLOGS="STOPPED-ZIPLOGS"

    STATE_STARTING="STARTING"
    STATE_STARTING_RESTORE="STARTING-RESTORE"

    STATE_STARTED="STARTED"         # reported as "running" from tabadmin
    STATE_STARTED_BACKUP="STARTED-BACKUP"
    # backup for/before restore
    STATE_STARTED_BACKUP_RESTORE="STARTED-BACKUP-RESTORE"
    # backup for/before stop
    STATE_STARTED_BACKUP_STOP="STARTED-BACKUP-STOP"
    STATE_STARTED_BACKUPDEL="STARTED-BACKUPDEL"
    STATE_STARTED_ZIPLOGS="STARTED-ZIPLOGS"

    STATE_STARTED_CLEANUP="STARTED-CLEANUP"
    STATE_STOPPED_CLEANUP="STOPPED-CLEANUP"

    STATE_DEGRADED="DEGRADED"       # reported from tabadmin

    STATE_UPGRADING="UPGRADING"       # agent or controller is upgrading

    STATE_UNKNOWN="UNKNOWN"        # no primary ever connected to the controller

    def __init__(self, server):
        self.server = server
        self.system = self.server.system
        self.config = self.server.config
        self.log = self.server.log
        self.envid = self.server.environment.envid

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
        try:
            return SystemManager(envid).get(SystemManager.SYSTEM_KEY_STATE)
        except ValueError, e:
            return StateManager.STATE_DISCONNECTED
