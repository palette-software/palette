from page import PalettePage

class Activity(PalettePage):
    TEMPLATE = 'workbook.mako'
    active = 'activity'

def make_activity(global_conf):
    return Activity(global_conf)
