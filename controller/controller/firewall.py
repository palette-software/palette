import json

class Firewall(object):

    URI = '/firewall'

    def __init__(self, agent):
        self.agent = agent
        self.server = agent.server

    def status(self):
        return self.server.send_immediate(self.agent, 'GET', self.URI)

    def enable(self, ports):
        port_commands = [{'action': 'enable', 'num': port} for port in ports]
        full_command = {'ports': port_commands}
        body = json.dumps(full_command)
        return self.server.send_immediate(self.agent, 'POST', self.URI, body)

    def disable(self, ports):
        port_commands = [{'action': 'disable', 'num': port} for port in ports]
        full_command = {'ports': port_commands}
        body = json.dumps(full_command)
        return self.server.send_immediate(self.agent, 'POST', self.URI, body)
