#!/usr/bin/env python

import SocketServer as socketserver

from agent import AgentManager

class CliHandler(socketserver.StreamRequestHandler):

    def error(self, msg, *args):
        if args:
            msg = msg % args
        print >> self.wfile, '[ERROR] '+msg

    def do_status(self, argv):
        print >> self.wfile, 'OK'

    def do_list(self, argv):
        if argv:
            self.error("'list' does not take any arguments")
            return
        print >> self.wfile, 'OK'
    
    def handle(self):
        while True:
            data = self.rfile.readline().strip()
            if not data: break

            argv = data.split()
            cmd = argv.pop(0)

            if not hasattr(self, 'do_'+cmd):
                self.error('invalid command: %s', cmd)
                continue

            f = getattr(self, 'do_'+cmd)
            f(argv)

class Controller(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == '__main__':
    
    manager = AgentManager()
    manager.start()

    HOST, PORT = 'localhost', 9000
    server = Controller((HOST, PORT), CliHandler)
    server.serve_forever()
    
