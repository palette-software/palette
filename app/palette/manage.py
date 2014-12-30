from webob import exc

from controller.profile import Role
from controller.palapi import CommException

from .page import PalettePage
from .rest import required_parameters, required_role, PaletteRESTApplication

class ManageApplication(PaletteRESTApplication):

    NAME = 'manage'

    # This method also implicity checks for missing parameters.
    def getbool(self, req, name):
        value = req.getbool(name, default=None)
        if value is None:
            raise exc.HTTPBadRequest("Invalid or missing parameter '"+name+"'")
        return value

    @required_role(Role.MANAGER_ADMIN)
    def handle_start(self, req):
        self.commapp.send_cmd('start', req=req, read_response=False)
        return {}

    @required_role(Role.MANAGER_ADMIN)
    def handle_stop(self, req):
        cmd = 'stop'
        if not self.getbool(req, 'backup'):
            cmd = cmd + ' nobackup'
        if not self.getbool(req, 'license'):
            cmd = cmd + ' nolicense'
        if not self.getbool(req, 'maint'):
            cmd = cmd + ' nomaint'
        self.commapp.send_cmd(cmd, req=req, read_response=False)
        return {}

    @required_role(Role.MANAGER_ADMIN)
    def handle_restart(self, req):
        cmd = 'restart'
        if not self.getbool(req, 'backup'):
            cmd = cmd + ' nobackup'
        if not self.getbool(req, 'license'):
            cmd = cmd + ' nolicense'
        self.commapp.send_cmd(cmd, req=req, read_response=False)
        return {}

    @required_role(Role.MANAGER_ADMIN)
    def handle_repair_license(self, req):
        self.commapp.send_cmd('license repair', req=req, read_response=False)
        return {}

    @required_role(Role.MANAGER_ADMIN)
    def handle_ziplogs(self, req):
        cmd = 'ziplogs'
        self.commapp.send_cmd(cmd, req=req, read_response=False)
        return {}

    @required_role(Role.MANAGER_ADMIN)
    def handle_restart_controller(self, req):
        self.commapp.send_cmd('exit', req=req, read_response=False)
        return {}

    @required_role(Role.MANAGER_ADMIN)
    def handle_restart_webserver(self, req):
        self.commapp.send_cmd('apache restart', req=req, read_response=False)
        return {}

    @required_parameters('action')
    def service(self, req):
        # pylint: disable=too-many-return-statements
        if req.method != "POST":
            raise exc.HTTPMethodNotAllowed()
        action = req.POST['action'].lower()
        try:
            if action == 'start':
                return self.handle_start(req)
            elif action == 'stop':
                return self.handle_stop(req)
            elif action == 'restart':
                return self.handle_restart(req)
            elif action == 'repair-license':
                return self.handle_repair_license(req)
            elif action == 'ziplogs':
                return self.handle_ziplogs(req)
            elif action == 'restart-webserver':
                return self.handle_restart_webserver(req)
            elif action == 'restart-controller':
                return self.handle_restart_controller(req)
        except CommException:
            raise exc.HTTPMethodNotAllowed()
        raise exc.HTTPBadRequest()


class Manage(PalettePage):
    TEMPLATE = 'manage.mako'
    active = 'manage'
    required_role = Role.READONLY_ADMIN

def make_manage(global_conf):
    return Manage(global_conf)
