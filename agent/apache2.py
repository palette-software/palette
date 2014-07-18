import os
import subprocess

class Apache2(object):

    CTLBIN = 'httpdctl'

    def __init__(self, conf, port, bindir=None):
        self.conf = conf
        if bindir:
            self.bindir = bindir
        else:
            bindir = os.path.join(os.path.dirname(__file__), 'bin')
            bindir = os.path.abspath(bindir)
        self.ctlbin = os.path.join(bindir, Apache2.CTLBIN)
        self.environ = os.environ.copy()
        self.setport(port)

    def start(self):
        cmd = [self.ctlbin, '-k', 'start']
        return subprocess.call(cmd, env=self.environ)

    def stop(self):
        cmd = [self.ctlbin, '-k', 'stop']
        return subprocess.call(cmd, env=self.environ)
        
    def setport(self, port):
        self.port = port
        self.environ['LISTEN_PORT'] = str(port)
