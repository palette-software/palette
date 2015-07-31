from webob import exc

from controller.profile import Role
from controller.palapi import CommException

from .page import PalettePage
from .rest import required_parameters, required_role, PaletteRESTApplication

class ManageApplication(PaletteRESTApplication):

    NAME = 'manage'

    @required_role(Role.MANAGER_ADMIN)
    def handle_start(self, req):
        self.commapp.send_cmd('start', req=req, read_response=False)
        return {}

    @required_parameters('backup', 'license')
    @required_role(Role.MANAGER_ADMIN)
    def handle_stop(self, req):
        cmd = 'stop'
        if not req.params_getbool('backup'):
            cmd = '/nobackup ' + cmd
        if not req.params_getbool('license'):
            cmd = '/nolicense ' + cmd
        cmd = '/nomaint ' + cmd  # Never enable the maintenance web server
        self.commapp.send_cmd(cmd, req=req, read_response=False)
        return {}

    @required_parameters('backup', 'license')
    @required_role(Role.MANAGER_ADMIN)
    def handle_restart(self, req):
        cmd = 'restart'
        if not req.params_getbool('backup'):
            cmd = '/nobackup ' + cmd
        if not req.params_getbool('license'):
            cmd = '/nolicense ' + cmd
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

    @required_role(Role.MANAGER_ADMIN)
    def handle_manual_update(self, req):
        import sys
        print >> sys.stderr, " *** MANUAL UPDATE *** "
        self.commapp.send_cmd("upgrade controller", req=req,
                                                      read_response=False)
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
            elif action == 'manual-update':
                return self.handle_manual_update(req)
        except CommException:
            raise exc.HTTPMethodNotAllowed()
        raise exc.HTTPBadRequest()


class ManagePage(PalettePage):
    TEMPLATE = 'manage.mako'
    active = 'manage'
    required_role = Role.READONLY_ADMIN

