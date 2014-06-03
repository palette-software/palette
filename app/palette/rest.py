import socket

from akiri.framework.api import RESTApplication
from akiri.framework.config import store

from controller.domain import Domain
from controller.system import SystemManager

class PaletteRESTHandler(RESTApplication):

    def __init__(self, global_conf):
        super(PaletteRESTHandler, self).__init__(global_conf)

        domainname = store.get('palette', 'domainname')
        self.domain = Domain.get_by_name(domainname)
        self.system = SystemManager(self.domain.domainid)
        self.telnet = Telnet(self)

    def base_path_info(self, req):
        # REST handlers return the handle path prefix too, strip it.
        path_info = req.environ['PATH_INFO']
        if path_info.startswith('/' + self.NAME):
            path_info = path_info[len(self.NAME)+1:]
        if path_info.startswith('/'):
            path_info = path_info[1:]
        return path_info

class Telnet(object):

    def __init__(self, app):
        self.app = app
        self.port = store.getint("palette", "telnet_port", default=9000)
        self.hostname = store.get("palette",
                                  "telnet_hostname",
                                  default="localhost")

    def send_cmd(self, cmd, sync=False):
        # Start and stop commands are always sent to the primary.
        preamble = "/domainid=%d /type=primary" % (self.app.domain.domainid)
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((self.hostname, self.port))
        s = conn.makefile('w+', 1)
        s.write(preamble + ' ' + cmd + '\n')
        s.flush()
        data = s.readline().strip()
        if data != 'OK':
            raise RuntimeError(data)
        if sync:
            data = s.readline()
        conn.close()
        return sync and data or None
