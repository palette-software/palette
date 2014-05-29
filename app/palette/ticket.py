from page import PalettePage

class Ticket(PalettePage):
    TEMPLATE = "ticket.mako"
    active = None

def make_ticket(global_conf):
    return Ticket(global_conf)
