import json

class Request(object):
    """Represents a request.
       Creates a body and adds:
        command: <command>
        xid: <xid>
        body: <body>
    """

    xid = 1     # fixme: this will eventually come from the database

    def __init__(self, action, send_body_dict = {}, xid = False):

        if xid:
            # User supplied an xid.  use it
            self.xid = xid
        else:
            Request.xid += 1
            self.xid = Request.xid

        send_body_dict["action"] = action
        send_body_dict["xid"] = self.xid
        self.send_body = json.dumps(send_body_dict)

    def __repr__(self):
        return "<action: %s, body_dict: %s, xid: %d>" % \
            (self.action, self.send_body, self.xid)

class Cli_Start_Request(Request):
    def __init__(self, cli_command):
            super(Cli_Start_Request, self).__init__("start", {"cli": cli_command})

class Copy_Start_Request(Request):
    def __init__(self, send_body_dict):
            super(Copy_Start_Request, self).__init__("start", send_body_dict)

class Cleanup_Request(Request):

    def __init__(self, xid):

        super(Cleanup_Request, self).__init__("cleanup", xid=xid)
