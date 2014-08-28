
class ODBC(object):

    URI = '/sql'

    DRIVER = '{PostgreSQL Unicode(x64)}'
    SERVER = '127.0.0.1'
    PORT = 8060
    DATABASE = 'workgroup'
    UID = 'tblwgadmin'
    PASSWD = ''

    def __init__(self, agent):
        self.agent = agent
        self.server = agent.server
        if self.server is None:
            raise RuntimeError("agent.server is None")

    def connection(self):
        s = 'DRIVER=' + self.DRIVER +'; '
        s += 'Server=' + self.SERVER + '; '
        s += 'Port=' + str(self.PORT) + '; '
        s += 'Database=' + self.DATABASE + '; '
        s += 'Uid=' + self.UID + '; '
        s += 'Pwd=' + self.PASSWD + ';'
        return s

    def execute(self, stmt):
        data = {'connection': self.connection(),
                'select-statement': stmt}
        return self.server.send_immediate(self.agent, 'POST', self.URI, data)
