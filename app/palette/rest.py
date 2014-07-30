import socket
from webob import exc

from akiri.framework.api import RESTApplication
from akiri.framework.config import store

from controller.domain import Domain
from controller.environment import Environment
from controller.system import SystemManager
from controller.profile import UserProfile, Role

def required_parameters(*params):
    def wrapper(f):
        def realf(self, req, *args):
            if req.method != 'POST':
                raise exc.HTTPMethodNotAllowed(req.method)
            for p in params:
                if p not in req.POST:
                    raise exc.HTTPBadRequest("'" + p + "' missing")
            return f(self, req, *args)
        return realf
    return wrapper

def required_role(name):
    def wrapper(f):
        def realf(self, req):
            if isinstance(name, basestring):
                role = Role.get_by_name(name).roleid
            else:
                role = Role.get_by_roleid(name)
            # FIXME: this should have to happen here.
            if isinstance(req.remote_user, basestring):
                req.remote_user = UserProfile.get_by_name(req.remote_user)
            if req.remote_user.roleid < role.roleid:
                raise exc.HTTPForbidden("The '"+role.name+"' role is required.")
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
        # FIXME: either do this or add envid (not both)
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

    def send_cmd(self, cmd, req=None, sync=False, displayname=None):
        preamble = "/domainid=%d " % self.app.domain.domainid
        if not displayname:
            # Send to the primary unless a displayname is specified
            preamble += "/type=primary"
        else:
            preamble += '/displayname="%s"' % displayname

        if req:
            if isinstance(req.remote_user, basestring):
                remote_user_profile = UserProfile.get_by_name(req.remote_user)
            else:
                # FIXME: in this case remote_user is the profile
                remote_user_profile = \
                                UserProfile.get_by_name(req.remote_user.name)

            userid = remote_user_profile.userid
            preamble += " /userid=%d" % userid

        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((self.hostname, self.port))
        s = conn.makefile('w+', 1)
        s.write(preamble + ' ' + cmd + '\n')
        s.flush()
        data = s.readline().strip()
        if data != 'OK':
            print "bad result for cmd '%s': %s" % (cmd, data)
            raise exc.HTTPServiceUnavailable
        elif sync:
            data = s.readline()
        conn.close()
        return sync and data or None
