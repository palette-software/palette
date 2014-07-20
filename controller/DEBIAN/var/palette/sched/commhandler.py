import sys 
import socket
import argparse
import json

class CommHandler(object):

    def __init__(self):

        parser = argparse.ArgumentParser(sys.argv[0])
        parser.add_argument('--hostname', dest='hostname', default='localhost')
        parser.add_argument('--port', dest='port', type=int, default=9000)
        parser.add_argument('--envid', dest='envid', type=int, default=1)

        args = parser.parse_args()

        self.hostname = args.hostname
        self.port = args.port
        self.envid = args.envid

        self.preamble = "/envid=%d /type=primary" % (self.envid)

    def send_cmd(self, cmd, sync=False, close=True, verbose=False):

        self.data = ""
        self.ddict = {}
        self.error = ""

        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((self.hostname, self.port))
        sock = conn.makefile('w+', 1)
        if verbose:
            print "Sending command:", cmd
        sock.write(self.preamble + ' ' + cmd + '\n')
        sock.flush()
        data = sock.readline().strip()
        print data
        if data != 'OK':
            sys.exit(1)
        if sync:
            self.data = sock.readline()
            try:
                self.ddict = json.loads(self.data)
            except ValueError as e:
                self.error = ("Can't decode input from cmd '%s' from " + \
                    "returned string '%s': %s") % (cmd, self.data, str(e))
                if close:
                    conn.close()
                return False

            if 'error' in self.ddict:
                self.error = self.ddict['error']
                if close:
                    conn.close()
                return False

        if close:
            conn.close()

        return True
