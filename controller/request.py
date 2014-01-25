import json

class Request(object):
    """Represents a request.
       Creates a body and adds:
        command: <command>
        xid: <xid>
        body: <body>
    """

    xid = 1     # fixme: this will eventually come from the database

    def __init__(self, action, send_body_dict = {}):

        Request.xid += 1
        self.xid = Request.xid
        send_body_dict["action"] = action
        send_body_dict["xid"] = Request.xid
        self.send_body = json.dumps(send_body_dict)

    def __repr__(self):
        return "<action: %s, body_dict: %s, xid: %d>" % \
            (self.action, self.send_body, self.xid)

class Cli_Request(Request):

    def __init__(self, action, cli_command=""):
        if action == 'start':
            super(Cli_Request, self).__init__(action, {"cli": cli_command})
        elif action == 'cleanup':
            super(Cli_Request, self).__init__(action)
        else:
            print "Cli_Request bad action:", action

