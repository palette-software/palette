from akiri.framework.api import UserInterfaceRenderer

class Ticket(UserInterfaceRenderer):
    TEMPLATE = "ticket.mako"
    active = None

def make_ticket(global_conf):
    return Ticket(global_conf)
