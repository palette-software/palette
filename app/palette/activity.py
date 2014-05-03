from akiri.framework.api import UserInterfaceRenderer

class Activity(UserInterfaceRenderer):
    TEMPLATE = 'activity.mako'
    main_active = 'activity'

def make_activity(global_conf):
    return Activity(global_conf)
