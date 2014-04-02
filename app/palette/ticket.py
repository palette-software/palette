from akiri.framework.api import UserInterfaceRenderer

class Ticket(UserInterfaceRenderer):

    TEMPLATE = "ticket.mako"
    def handle(self, req):
        return None

def make_ticket(global_conf):
    return Ticket(global_conf)
