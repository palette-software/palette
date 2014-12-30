from akiri.framework.route import Router

# TEMP
from .request import System
from controller.environment import Environment
from controller.profile import UserProfile

# FIXME: this is mostly duplicate with request.py
def req_getattr(req, name):
    if name == 'envid':
        if not 'PALETTE_ENVIRONMENT' in req.environ:
            req.environ['PALETTE_ENVIRONMENT'] = Environment.get()
        return req.environ['PALETTE_ENVIRONMENT'].envid
    if name == 'system':
        return System(req.envid)

    raise AttributeError(name)

class RestRouter(Router):
    """
    Temporary class to override the request getattr function.
    The setup will eventually be handled by a dedicated WSGI function.
    """
    def service(self, req):
        req.getattr = req_getattr
        req.remote_user = UserProfile.get_by_name(req.envid,
                                                  req.remote_user)
        return super(RestRouter, self).service(req)

from .environment import EnvironmentApplication
from .general import GeneralApplication
from .manage import ManageApplication
from .monitor import MonitorApplication
from .profile import ProfileApplication
from .server import ServerApplication
from .user import UserApplication
from .yml import YmlApplication
from .workbooks import WorkbookApplication

def make_rest(global_conf):
    # pylint: disable=unused-argument
    app = RestRouter()
    app.add_route(r'/environment\Z', EnvironmentApplication())
    app.add_route(r'/general?(/(?P<action>[^\s]+))?\Z',
                  GeneralApplication())
    app.add_route(r'/manage\Z', ManageApplication())
    app.add_route(r'/monitor\Z', MonitorApplication())
    app.add_route(r'/profile\Z', ProfileApplication())
    app.add_route(r'/servers?(/(?P<action>[^\s]+))?\Z',
                  ServerApplication())
    app.add_route(r'/users?(/(?P<action>[^\s]+))?\Z',
                  UserApplication())
    app.add_route(r'/yml\Z', YmlApplication())
    app.add_route(r'/workbooks?(/(?P<action>[^\s]+))?\Z',
                  WorkbookApplication())
    return app
