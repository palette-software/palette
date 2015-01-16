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



class PaletteRouter(Router):
    """
    Temporary class to override the request getattr function.
    The setup will eventually be handled by a dedicated WSGI function.
    """
    def service(self, req):
        # FIXME: don't override the existing remote_user, instead create
        # a different member like 'remote_user_profile'.
        req.getattr = req_getattr
        req.remote_user = UserProfile.get_by_name(req.envid,
                                                  req.remote_user)
        return super(PaletteRouter, self).service(req)

from .backup import BackupApplication
from .environment import EnvironmentApplication
from .gcs import GCSApplication
from .general import GeneralApplication
from .manage import ManageApplication
from .monitor import MonitorApplication
from .profile import ProfileApplication
from .setup import SetupApplication
from .server import ServerApplication
from .s3 import S3Application
from .user import UserApplication
from .yml import YmlApplication
from .workbooks import WorkbookApplication

def make_rest(global_conf):
    # pylint: disable=unused-argument
    app = PaletteRouter()
    app.add_route(r'/backup\Z', BackupApplication())
    app.add_route(r'/environment\Z', EnvironmentApplication())
    app.add_route(r'/gcs\Z', GCSApplication())
    app.add_route(r'/general\Z|/general/', GeneralApplication())
    app.add_route(r'/manage\Z', ManageApplication())
    app.add_route(r'/monitor\Z', MonitorApplication())
    app.add_route(r'/profile\Z', ProfileApplication())
    app.add_route(r'/s3\Z', S3Application())
    app.add_route(r'/setup\Z|/setup/', SetupApplication())
    app.add_route(r'/servers?(/(?P<action>[^\s]+))?\Z',
                  ServerApplication())
    app.add_route(r'/users?(/(?P<action>[^\s]+))?\Z',
                  UserApplication())
    app.add_route(r'/yml\Z', YmlApplication())
    app.add_route(r'/workbooks?(/(?P<action>[^\s]+))?\Z',
                  WorkbookApplication())
    return app

from .setup import SetupConfigPage
from .general import GeneralPage
from .server import ServerConfigPage
from .user import UserConfigPage
from .yml import YmlPage

def make_configure(global_conf):
    # pylint: disable=unused-argument
    app = Router()
    app.add_route(r'/setup\Z', SetupConfigPage(None))
    app.add_route(r'/general\Z', GeneralPage(None))
    app.add_route(r'/servers?\Z', ServerConfigPage(None))
    app.add_route(r'/users?\Z', UserConfigPage(None))
    app.add_route(r'/yml\Z', YmlPage(None))
    return app
