import sys
from webob import exc

from akiri.framework.api import Page
from akiri.framework import GenericWSGI
from akiri.framework.proxy import JSONProxy
from akiri.framework.route import Router
# pylint: disable=import-error,no-name-in-module
from akiri.framework.ext.sqlalchemy import meta

from collections import OrderedDict

from controller.profile import UserProfile, Role
from controller.passwd import tableau_hash
from controller.general import SystemConfig
from controller.util import extend

from .page import PalettePage
from .option import DictOption
from .rest import PaletteRESTApplication, required_parameters


# FIXME: add required_role to all the GET/POST handlers.

def dump(req):
    print >> sys.stderr, str(req)

class SetupPage(Page):
    TEMPLATE = "setup.mako"

    def render(self, req, obj=None):
        return super(SetupPage, self).render(req, obj=obj)

def make_setup(global_conf):
    return SetupPage(global_conf)


class SetupConfigPage(PalettePage):
    TEMPLATE = "config/setup.mako"
    active = 'setup'
    expanded = True
    required_role = Role.MANAGER_ADMIN

def make_setup_config(global_conf):
    return SetupConfigPage(global_conf)


class MailServerType(DictOption):
    """Representation of the 'Mail Server Type' dropdown."""
    NAME = 'mail-server-type'
    DIRECT = 1
    RELAY = 2
    NONE = 3

    def __init__(self, valueid):
        options = OrderedDict({})
        options[self.DIRECT] = 'Direct SMTP Mail Server (Default)'
        options[self.RELAY] = 'Relay SMTP Mail Server Settings'
        options[self.NONE] = 'None'
        super(MailServerType, self).__init__(self.NAME, valueid, options)


class AuthType(DictOption):
    """Representation of the 'Authentication' dropdown."""
    NAME = 'authentication-type'
    TABLEAU = 1
    ACTIVE_DIRECTORY = 2
    LOCAL = 3

    def __init__(self, valueid):
        options = OrderedDict({})
        options[self.TABLEAU] = "Tableau Server's Configured Authentication"
        options[self.ACTIVE_DIRECTORY] = "Active Directory"
        options[self.LOCAL] = "Tableau Local Authentication"
        super(AuthType, self).__init__(self.NAME, valueid, options)


class BaseSetupApplication(PaletteRESTApplication):
    pass


class SetupURLApplication(BaseSetupApplication):
    """Handler for the 'SERVER URL' section."""

    def service_GET(self, req):
        # pylint: disable=unused-argument
        scfg = SystemConfig(req.system)

        return {'server-url': scfg.server_url}

    @required_parameters('server-url')
    def service_POST(self, req):
        url = req.params_get('server-url')
        req.system.save(SystemConfig.SERVER_URL, url)
        return {'server-url': url}


class SetupAdminApplication(BaseSetupApplication):
    """Handler for the 'AUTHENTICATION' section."""

    PASSWD = '********'

    def service_GET(self, req):
        # pylint: disable=unused-argument
        entry = meta.Session.query(UserProfile).\
            filter(UserProfile.name == 'palette').one()

        if entry.hashed_password:
            passwd = self.PASSWD
        else:
            passwd = ''
        return {'password': passwd}

    @required_parameters('password')
    def service_POST(self, req):
        passwd = req.params_get('password')
        hashed_password = tableau_hash(passwd, '')
        meta.Session.query(UserProfile).\
            filter(UserProfile.name == 'palette').\
            update({"hashed_password": hashed_password},
                    synchronize_session=False)

        meta.Session.commit()

        return {'password': passwd}


class SetupMailApplication(JSONProxy):

    def __init__(self):
        super(SetupMailApplication, self).__init__('http://localhost:9091', \
                                    allowed_request_methods=('GET', 'POST'))

    def postprocess(self, req, data):
        if 'error' in data:
            return data

        req.system.save(SystemConfig.FROM_EMAIL, data['from_email'])
        req.system.save(SystemConfig.MAIL_DOMAIN, data['mail_domain'])
        req.system.save(SystemConfig.MAIL_SERVER_TYPE, data['mail_server_type'])

        if data['mail_server_type'] == '2':
            req.system.save(SystemConfig.MAIL_SMTP_SERVER, data['smtp_server'])
            req.system.save(SystemConfig.MAIL_SMTP_PORT, data['smtp_port'])
            req.system.save(SystemConfig.MAIL_USERNAME, data['smtp_username'])
            req.system.save(SystemConfig.MAIL_PASSWORD, data['smtp_password'])
        else:
            req.system.save(SystemConfig.MAIL_SMTP_SERVER, "")
            req.system.save(SystemConfig.MAIL_SMTP_PORT, "")
            req.system.save(SystemConfig.MAIL_USERNAME, "")
            req.system.save(SystemConfig.MAIL_PASSWORD, "")
        return data

    def service_GET(self, req):
        # pylint: disable=unused-argument
        scfg = SystemConfig(req.system)

        mail_server_type = req.system.get(scfg.MAIL_SERVER_TYPE, default=None)
        if mail_server_type == str(MailServerType.DIRECT):
            mst = MailServerType(MailServerType.DIRECT)
        elif mail_server_type == str(MailServerType.RELAY):
            mst = MailServerType(MailServerType.RELAY)
        else:
            mail_server_type = str(MailServerType.NONE)
            mst = MailServerType(MailServerType.NONE)
        config = [mst.default()]
        data = {'config': config}

        parts = scfg.from_email.rsplit(" ", 1)
        if len(parts) == 2:
            data['alert-email-name'] = parts[0]
            del parts[0]
        else:
            data['alert-email-name'] = ""

        data['alert-email'] = parts[0]

        #data['mail-server-type'] = scfg.mail_server_type
        data['mail-server-type'] = int(mail_server_type)
        # data['smtp-server'] = scfg.mail_smtp_server
        _ = req.system.getint(scfg.MAIL_SMTP_PORT, default=None)
        if not _ is None:
            data['smtp-port'] = _
        # data['smtp-username'] = scfg.mail_username
        _ = req.system.getint(scfg.MAIL_USERNAME, default=None)
        if not _ is None:
            data['smtp-username'] = _
        _ = req.system.getint(scfg.MAIL_PASSWORD, default=None)
        if not _ is None:
            data['smtp-password'] = '********' # FIXME

        return data

    def service(self, req):
        if req.method == 'GET':
            return self.service_GET(req)
        elif req.method == 'POST':
            return super(SetupMailApplication, self).service(req)
        else:
            raise exc.HTTPMethodNotAllowed()


class SetupSSLApplication(BaseSetupApplication):
    """Handler for the 'SERVER SSL CERTIFICATE' section."""

    def service_GET(self, req):
        # pylint: disable=unused-argument
        data = {}
        data['enable-ssl'] = True # FIXME
        return data

    def service_POST(self, req):
        dump(req)
        enable_ssl = req.params_getbool('enable-ssl')
        if enable_ssl == None:
            raise exc.HTTPBadRequest()
        # FIXME: save value
        # FIXME: save cert, cert key, cert chain
        return {'enable-ssl': enable_ssl}


class SetupAuthApplication(BaseSetupApplication):
    """Handler for the 'AUTHENTICATION' section."""

    def service_GET(self, req):
        # pylint: disable=unused-argument
        scfg = SystemConfig(req.system)
        auth_type = scfg.authentication_type
        if auth_type == 1:
            atype = AuthType(AuthType.TABLEAU)
        elif auth_type == 2:
            atype = AuthType(AuthType.ACTIVE_DIRECTORY)
        else:
            atype = AuthType(AuthType.LOCAL)

        config = [atype.default()]
        data = {'config': config}
        return data

    def service_POST(self, req):
        dump(req)
        authtype = req.params_getint('authentication-type')
        if authtype == None:
            raise exc.HTTPBadRequest()
        req.system.save(SystemConfig.AUTHENTICATION_TYPE, authtype)
        return {'authentication-type': authtype}


class _SetupApplication(BaseSetupApplication):
    """Handler for initial page GET requests."""

    def __init__(self):
        super(_SetupApplication, self).__init__()
        self.admin = SetupAdminApplication()
        self.mail = SetupMailApplication()
        self.ssl = SetupSSLApplication()
        self.auth = SetupAuthApplication()
        self.url = SetupURLApplication()

    def service_GET(self, req):
        data = {}
        extend(data, self.admin.service_GET(req))
        extend(data, self.mail.service_GET(req))
        extend(data, self.ssl.service_GET(req))
        extend(data, self.auth.service_GET(req))
        extend(data, self.url.service_GET(req))
        return data


class SetupMailTestApplication(BaseSetupApplication):
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
        self.add_route(r'/admin\Z', SetupAdminApplication())
        self.add_route(r'/auth\Z|/authenticate\Z', SetupAuthApplication())
        self.add_route(r'/ssl\Z|/SSL\Z', SetupSSLApplication())
        self.add_route(r'/mail\Z', SetupMailApplication())
        self.add_route(r'/mail/test\Z', SetupMailTestApplication())
        self.add_route(r'/admin\Z', SetupURLApplication())
        self.add_route(r'/url\Z', SetupURLApplication())


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
