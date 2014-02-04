
from webob import exc

from akiri.framework.api import RESTApplication, DialogPage

class ManageApplication(RESTApplication):

    NAME = 'manage'

    def handle_start(self, req):
        return {}

    def handle_stop(self, req):
        return {}

    def handle(self, req):
        if req.method != "POST":
            raise exc.HTTPMethodNotAllowed()
        action = req.POST['action'].lower()
        if action == 'start':
            return self.handle_start(req)
        elif action == 'stop':
            return self.handle_stop(req)
        raise exc.HTTPBadRequest()
        
class ManageAdvancedDialog(DialogPage):

    NAME = "manage"
    TEMPLATE = "manage.mako"

    def __init__(self, global_conf):
        super(ManageAdvancedDialog, self).__init__(global_conf)
        self.agents = ["primary", "other"]
