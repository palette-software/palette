from webob import exc

from controller.profile import Role

from page import PalettePage
from rest import PaletteRESTHandler, required_parameters, required_role

class ManageApplication(PaletteRESTHandler):

    NAME = 'manage'

    # This method also implicity checks for missing parameters.
    def getbool(self, req, name):
        try:
            value = req.POST[name].lower()
            if value == 'true' or value == '1':
                return True
            if value == 'false' or value == '0':
                return False
        except (TypeError, ValueError):
            pass
        raise exc.HTTPBadRequest("Invalid or missing parameter '"+name+"'")

    @required_role(Role.MANAGER_ADMIN)
    def handle_start(self, req):
        self.telnet.send_cmd('start', req=req)
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
        self.telnet.send_cmd(cmd, req=req)
        return {}

    @required_role(Role.MANAGER_ADMIN)
    def handle_repair_license(self, req):
        self.telnet.send_cmd('license repair', req=req)
        return {}

    @required_parameters('action')
    def handle(self, req):
        if req.method != "POST":
            raise exc.HTTPMethodNotAllowed()
        action = req.POST['action'].lower()
        if action == 'start':
            return self.handle_start(req)
        elif action == 'stop':
            return self.handle_stop(req)
        elif action == 'repair-license':
            return self.handle_repair_license(req)
        raise exc.HTTPBadRequest()


class Manage(PalettePage):
    TEMPLATE = 'manage.mako'
    active = 'manage'
    required_role = Role.READONLY_ADMIN

def make_manage(global_conf):
    return Manage(global_conf)
