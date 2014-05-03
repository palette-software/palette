from akiri.framework.api import UserInterfaceRenderer

class Ticket(UserInterfaceRenderer):

    TEMPLATE = "ticket.mako"
    main_active = None

def make_ticket(global_conf):
    return Ticket(global_conf)
