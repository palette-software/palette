from webob import exc

from controller.profile import Role
from controller.palapi import CommException

from .page import PalettePage
from .rest import required_parameters, required_role, status_ok, status_failed
from .rest import PaletteRESTApplication
from .backup import RestoreMixin

class ManageApplication(PaletteRESTApplication, RestoreMixin):

    NAME = 'manage'

    @required_role(Role.MANAGER_ADMIN)
    def handle_start(self, req):
        sync = req.params_getbool('sync', default=False)
        self.commapp.send_cmd('start', req=req, read_response=sync)
        return {'status': 'OK'}

    @required_role(Role.MANAGER_ADMIN)
    def handle_stop(self, req):
        sync = req.params_getbool('sync', default=False)
        cmd = 'stop'
        if not req.params_getbool('backup', default=False):
            cmd = '/nobackup ' + cmd
        if not req.params_getbool('license', default=False):
            cmd = '/nolicense ' + cmd
        cmd = '/nomaint ' + cmd  # Never enable the maintenance web server
        self.commapp.send_cmd(cmd, req=req, read_response=sync)
        return status_ok()

    @required_role(Role.MANAGER_ADMIN)
    def handle_restart(self, req):
        sync = req.params_getbool('sync', default=False)
        cmd = 'restart'
        if not req.params_getbool('backup', default=False):
            cmd = '/nobackup ' + cmd
        if not req.params_getbool('license', default=False):
            cmd = '/nolicense ' + cmd
        self.commapp.send_cmd(cmd, req=req, read_response=sync)
        return status_ok()

    @required_role(Role.MANAGER_ADMIN)
    def handle_backup(self, req):
        """ Do a backup (duplicated in backup.py) """
        sync = req.params_getbool('sync', default=False)
        self.commapp.send_cmd('backup', req=req, read_response=sync)
        if sync:
            return self.commapp.result
        return status_ok()

    @required_role(Role.MANAGER_ADMIN)
    def handle_repair_license(self, req):
        sync = req.params_getbool('sync', default=False)
        self.commapp.send_cmd('license repair', req=req, read_response=sync)
        return status_ok()

    @required_role(Role.MANAGER_ADMIN)
    def handle_ziplogs(self, req):
        sync = req.params_getbool('sync', default=False)
        cmd = 'ziplogs'
        self.commapp.send_cmd(cmd, req=req, read_response=sync)
        return status_ok()

    @required_role(Role.MANAGER_ADMIN)
    def handle_restart_controller(self, req):
        self.commapp.send_cmd('exit', req=req, read_response=False)
        return status_ok()

    @required_role(Role.MANAGER_ADMIN)
    def handle_restart_webserver(self, req):
        self.commapp.send_cmd('apache restart', req=req, read_response=False)
        return status_ok()

    @required_role(Role.MANAGER_ADMIN)
    def handle_manual_update(self, req):
        import sys
        print >> sys.stderr, " *** MANUAL UPDATE *** "
        self.commapp.send_cmd("upgrade controller", req=req,
                              read_response=False)
        return status_ok()

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
            elif action == 'backup':
                return self.handle_backup(req)
            elif action == 'restore':
                return self.handle_restore(req)
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
        except CommException, ex:
            result = status_failed(ex.message)
            result['errno'] = ex.errnum
            return result
        raise exc.HTTPBadRequest()


class ManagePage(PalettePage):
    TEMPLATE = 'manage.mako'
    active = 'manage'
    required_role = Role.READONLY_ADMIN

