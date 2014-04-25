import json

class Firewall(object):

    URI = '/firewall'

    def __init__(self, agent):
        self.agent = agent
        self.server = agent.server

    def status(self):
        return self.server.send_immediate(self.agent, 'GET', self.URI)

    def enable(self, port):
        d = {'ports': [{'action':'enable', 'num':port}]}
        body = json.dumps(d)
        return self.server.send_immediate(self.agent, 'POST', self.URI, body)

    def disable(self, port):
        d = {'ports': [{'action':'disable', 'num':port}]}
        body = json.dumps(d)
        return self.server.send_immediate(self.agent, 'POST', self.URI, body)
