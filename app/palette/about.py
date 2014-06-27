from page import PalettePage

class About(PalettePage):
    TEMPLATE = 'about.mako'
    active = 'about'
    expanded = True

def make_about(global_conf):
    return About(global_conf)
