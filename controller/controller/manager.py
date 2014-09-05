
class Manager(object):

    def __init__(self, server):
        self.server = server
        self.envid = self.server.environment.envid
        self.log = self.server.log
