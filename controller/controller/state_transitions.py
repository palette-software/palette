from state import StateManager
from event_control import EventControl

STATUS_RUNNING = "RUNNING"
STATUS_STOPPED = "STOPPED"
STATUS_DEGRADED = "DEGRADED"

TRANSITIONS = {
    # Defines the new state and events to send based on the
    # old state new tableau status.

    # Old state
    StateManager.STATE_PENDING: {
        # New Tableau status
        STATUS_RUNNING:
            # new state
            {'state': StateManager.STATE_STARTED,
            # event(s) to generate, if any.
            'events': EventControl.INIT_STATE_STARTED},

        STATUS_STOPPED:
            {'state': StateManager.STATE_STOPPED,
             'events': EventControl.INIT_STATE_STOPPED},

        STATUS_DEGRADED:
            {'state': StateManager.STATE_DEGRADED,
             'events': EventControl.INIT_STATE_DEGRADED}
    },
    StateManager.STATE_STOPPED: {
        STATUS_RUNNING:
            {'state': StateManager.STATE_STARTED,
             'events': EventControl.STATE_UNEXPECTED_STATE_STARTED,
             'maint-stop': True},    # stop the maint server

        STATUS_STOPPED:
                {}, # no state change and no events to send.
        STATUS_DEGRADED:
            {'state': StateManager.STATE_DEGRADED,
             'events': [EventControl.STATE_UNEXPECTED_STATE_STARTED,
                        EventControl.STATE_DEGRADED],
             'maint-stop': True}    # stop the maint server
    },
    StateManager.STATE_STOPPED_UNEXPECTED: {
        STATUS_RUNNING:
            {'state': StateManager.STATE_STARTED,
             'events': EventControl.STATE_UNEXPECTED_STATE_STARTED,
             'maint-stop': True},
        STATUS_STOPPED:
                {}, # no state change and no events to send.
        STATUS_DEGRADED:
            {'state': StateManager.STATE_DEGRADED,
             'events': [EventControl.STATE_UNEXPECTED_STATE_STARTED,
                        EventControl.STATE_DEGRADED],
             'maint-stop': True}    # stop the maint server
    },
    StateManager.STATE_STARTED: {
        STATUS_RUNNING: {},
        STATUS_STOPPED:
            {'state': StateManager.STATE_STOPPED_UNEXPECTED,
             'events': EventControl.STATE_UNEXPECTED_STATE_STOPPED},
        STATUS_DEGRADED:
            {'state': StateManager.STATE_DEGRADED,
             'events': EventControl.STATE_DEGRADED},
    },
    StateManager.STATE_DEGRADED: {
        STATUS_RUNNING:
            {'state': StateManager.STATE_STARTED,
             'events': EventControl.STATE_STARTED_AFTER_DEGRADED},
        STATUS_STOPPED:
            {'state': StateManager.STATE_STOPPED_UNEXPECTED,
             'events': EventControl.STATE_UNEXPECTED_STATE_STOPPED},
        STATUS_DEGRADED:
            {'events': EventControl.STATE_DEGRADED}, # actually sends only once
    }
}
