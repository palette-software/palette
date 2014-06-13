import sys 
import socket
import argparse

class CommHandler(object):

    def __init__(self):

        parser = argparse.ArgumentParser(description="backup")
        parser.add_argument('--hostname', dest='hostname', default='localhost')
        parser.add_argument('--port', dest='port', default=9000)
        parser.add_argument('--envid', dest='envid', default=1)

        args = parser.parse_args()

        self.hostname = args.hostname
        self.port = args.port
        self.envid = args.envid

        self.preamble = "/envid=%s /type=primary" % (self.envid)

    def send_cmd(self, cmd, sync=False):

        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((self.hostname, self.port))
        sock = conn.makefile('w+', 1)
        sock.write(self.preamble + ' ' + cmd + '\n')
        sock.flush()
        data = sock.readline().strip()
        print data
        if data != 'OK':
            sys.exit(1)
        if sync:
            data = sock.readline()
        conn.close()
        return sync and data or None
