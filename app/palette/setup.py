from webob import exc

from akiri.framework.api import Page
from akiri.framework import GenericWSGI
from akiri.framework.proxy import JSONProxy
from akiri.framework.route import Router

from collections import OrderedDict

from controller.profile import UserProfile

from .page import PalettePage
from .option import BaseStaticOption
from .rest import PaletteRESTApplication

class SetupPage(Page):
    TEMPLATE = "setup.mako"

    def render(self, req, obj=None):
        return super(SetupPage, self).render(req, obj=obj)

def make_setup(global_conf):
    return SetupPage(global_conf)


class SetupConfigPage(PalettePage):
    TEMPLATE = "config/setup.mako"
    active = 'setup'

def make_setup_config(global_conf):
    return SetupConfigPage(global_conf)


class MailServerType(BaseStaticOption):

    NAME = 'mail-server-type'

    DIRECT = 1
    RELAY = 2
    NONE = 3

    @classmethod
    def items(cls):
        return OrderedDict({cls.DIRECT: 'Direct SMTP Mail Server (Default)',
                            cls.RELAY: 'Relay SMTP Mail Server Settings',
                            cls.NONE: 'None'})

class BaseSetupApplication(PaletteRESTApplication):
    pass


class _SetupApplication(BaseSetupApplication):

    def service_GET(self, req):
        # pylint: disable=unused-argument
        config = [MailServerType.config(MailServerType.DIRECT)]
        data = {'config': config}
        return data


class MailApplication(JSONProxy):

    def __init__(self):
        super(MailApplication, self).__init__('http://localhost:9090', \
                                    allowed_request_methods=('GET', 'POST'))

    def postprocess(self, req, data):
        data['proxy'] = 'Added by ' + __file__
        return data


class MailTestApplication(BaseSetupApplication):
    pass


class SetupApplication(Router):
    """
    This is the main handler for /rest/setup, but it just delegates to
    helper applications for the particular URL.  This is a hybrid approach
    to routing using both Traveral and URL dispatch.
    """
    def __init__(self):
        super(SetupApplication, self).__init__()
        self.add_route(r'/\Z', _SetupApplication())
        self.add_route(r'/mail\Z', MailApplication())
        self.add_route(r'/mail/test\Z', MailTestApplication())


class SetupTestApp(GenericWSGI):
    """ WSGI Middleware to test whether the system has been initially setup."""
    def service(self, req):
        if 'REMOTE_USER' in req.environ:
            # If REMOTE_USER is set - presumably from auth_tkt,
            # then setup has already been done.
            return None
        entry = UserProfile.get(req.envid, 0) # user '0', likely 'palette'
        if not entry.password:
            raise exc.HTTPTemporaryRedirect(location='/setup')
        return None

def make_setup_test(app, global_conf):
    # pylint: disable=unused-argument
    return SetupTestApp(app)
