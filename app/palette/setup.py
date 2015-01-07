from webob import exc

from akiri.framework.api import Page
from akiri.framework import GenericWSGI

from collections import OrderedDict

from controller.profile import UserProfile

from .option import BaseStaticOption
from .rest import PaletteRESTApplication

class SetupPage(Page):
    TEMPLATE = "setup.mako"

    def render(self, req, obj=None):
        return super(SetupPage, self).render(req, obj=obj)

def make_setup(global_conf):
    return SetupPage(global_conf)


class MailServerType(BaseStaticOption):

    NAME = 'mail-server-type'

    DIRECT = 1
    RELAY = 2
    NONE = 3

    @classmethod
    def items(cls):
        return OrderedDict({cls.DIRECT: 'Direct SMTP Mail Server (Default)',
                            cls.RELAY: 'Relay SMTP Mail Server Settings',
                            cls.NONE:   'None'})


class SetupApplication(PaletteRESTApplication):

    def handle_GET(self, req):
        # pylint: disable=unused-argument
        config = [MailServerType.config(MailServerType.DIRECT)]
        data = {'config': config}
        return data

    def test_email(self, req):
        if req.method == 'POST':
            print req.POST
        return {}

    def service(self, req):
        if 'action' in req.environ:
            action = req.environ['action']
            if action == 'email':
                return self.test_email(req)
            raise exc.HTTPNotFound()

        if req.method == 'GET':
            return self.handle_GET(req)
        elif req.method == 'POST':
            return {}
        else:
            raise exc.HTTPMethodNotAllowed()

class SetupTestApp(GenericWSGI):

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
