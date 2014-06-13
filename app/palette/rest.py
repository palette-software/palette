import socket
from webob import exc

from akiri.framework.api import RESTApplication
from akiri.framework.config import store

from controller.domain import Domain
from controller.environment import Environment
from controller.system import SystemManager

def required_parameters(*params):
    def wrapper(f):
        def realf(self, req):
            for p in params:
                if p not in req.POST:
                    raise exc.HTTPBadRequest("'" + p + "' missing")
            return f(self, req)
        return realf
    return wrapper

class PaletteRESTHandler(RESTApplication):

    def __init__(self, global_conf):
        super(PaletteRESTHandler, self).__init__(global_conf)
        self.telnet = Telnet(self)
        self.envid = Environment.get().envid

    def __getattr__(self, name):
        if name == 'domainname':
            return store.get('palette', 'domainname')
        if name == 'domain':
            return Domain.get_by_name(self.domainname)
        if name == 'environment':
            return Environment.get()
        if name == 'system':
            return SystemManager(self.envid)
        raise AttributeError(name)

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
            print "bad result:", data
            raise RuntimeError(data)
        if sync:
            data = s.readline()
        conn.close()
        return sync and data or None
