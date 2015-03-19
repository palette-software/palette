import sys
from webob import exc
from pytz import common_timezones as timezones
from urlparse import urlparse

from akiri.framework.proxy import JSONProxy
from akiri.framework.route import Router
import akiri.framework.sqlalchemy as meta

from collections import OrderedDict

from controller.profile import UserProfile, Role
from controller.passwd import tableau_hash
from controller.general import SystemConfig
from controller.util import extend
from controller.credential import CredentialEntry

from .page import Page, PalettePage
from .option import DictOption
from .rest import PaletteRESTApplication, required_parameters, required_role
from .mixin import CredentialMixin

def dump(req):
    print >> sys.stderr, str(req)

class SetupPage(Page):
    TEMPLATE = "setup.mako"


class SetupConfigPage(PalettePage):
    TEMPLATE = "config/setup.mako"
    active = 'setup'
    expanded = True
    required_role = Role.MANAGER_ADMIN


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

    @required_role(Role.MANAGER_ADMIN)
    def service(self, req):
        # Requires manager admin for all subclasses.
        return super(BaseSetupApplication, self).service(req)


class SetupURLApplication(BaseSetupApplication):
    """Handler for the 'SERVER URL' section."""

    def service_GET(self, req):
        # pylint: disable=unused-argument
        scfg = SystemConfig(req.system)

        url = scfg.server_url

        # FIXME (later): allow non-443 ports?
        if url == 'https://localhost':
            url = 'https://' + req.environ['HTTP_HOST']
            req.system.save(SystemConfig.SERVER_URL, url)

        return {'server-url': url}

    # FIXME: move to initial
    @required_parameters('server-url')
    def service_POST(self, req):
        url = req.params_get('server-url')
        result = urlparse(url)
        url = 'https://%s' % result.netloc
        req.system.save(SystemConfig.SERVER_URL, url)
        return {'server-url': url}

class SetupTableauURLApplication(BaseSetupApplication):
    """Handler for the 'TABLEAU SERVER URL' section."""

    def service_GET(self, req):
        # pylint: disable=unused-argument
        scfg = SystemConfig(req.system)
        return {'tableau-server-url': scfg.tableau_server_url}

    # FIXME: move to initial
    @required_parameters('tableau-server-url')
    def service_POST(self, req):
        url = req.params_get('tableau-server-url')
        req.system.save(SystemConfig.TABLEAU_SERVER_URL, url)
        return {'tableau-server-url': url}

class SetupAdminApplication(BaseSetupApplication):
    """Handler for the 'AUTHENTICATION' section."""

    def service_GET(self, req):
        # pylint: disable=unused-argument
        return {}

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


class SetupReadOnlyApplication(BaseSetupApplication, CredentialMixin):
    """Handler for setting the password of the read-only tableau user"""

    def service_GET(self, req):
        cred = self.get_cred(req.envid, self.READONLY_KEY)
        if not cred:
            return {}
        return {'readonly-password': cred.getpasswd()}

    @required_parameters('readonly-password')
    def service_POST(self, req):
        passwd = req.params_get('readonly-password')

        session = meta.Session()
        cred = self.get_cred(req.envid, self.READONLY_KEY)
        if not cred:
            if not passwd:
                return {'readonly-password': passwd}
            cred = CredentialEntry(envid=req.envid, key=self.READONLY_KEY)
            session.add(cred)

        if passwd:
            cred.user = self.READONLY_KEY
            cred.setpasswd(passwd)
        else:
            session.delete(cred)
        session.commit()
        return {'readonly-password': passwd}


class SetupMailApplication(JSONProxy, PaletteRESTApplication):

    def __init__(self):
        JSONProxy.__init__(self, 'http://localhost:9091',
                                    allowed_request_methods=('GET', 'POST'))
        PaletteRESTApplication.__init__(self)

    def postprocess(self, req, data):
        if 'error' in data:
            return data

        self._save_config(req, data)
        if 'smtp-password' in data:
            del data['smtp-password']
        return data

    def _save_config(self, req, data):
        """Save the configuration to the system table."""
        req.system.save(SystemConfig.MAIL_SERVER_TYPE,
                                            str(data['mail-server-type']))

        if data['mail-server-type'] != MailServerType.NONE:
            req.system.save(SystemConfig.FROM_EMAIL, data['from-email'])
            req.system.save(SystemConfig.MAIL_DOMAIN, data['mail-domain'])

        if data['mail-server-type'] == MailServerType.RELAY:
            req.system.save(SystemConfig.MAIL_SMTP_SERVER, data['smtp-server'])
            req.system.save(SystemConfig.MAIL_SMTP_PORT, str(data['smtp-port']))
            req.system.save(SystemConfig.MAIL_USERNAME, data['smtp-username'])
            req.system.save(SystemConfig.MAIL_PASSWORD, data['smtp-password'])
        else:
            req.system.delete(SystemConfig.MAIL_SMTP_SERVER)
            req.system.delete(SystemConfig.MAIL_SMTP_PORT)
            req.system.delete(SystemConfig.MAIL_USERNAME)
            req.system.delete(SystemConfig.MAIL_PASSWORD)

    def service_GET(self, req):
        # pylint: disable=bad-builtin
        scfg = SystemConfig(req.system)

        mail_server_type = scfg.mail_server_type

        if mail_server_type == str(MailServerType.DIRECT):
            mst = MailServerType(MailServerType.DIRECT)
        elif mail_server_type == str(MailServerType.RELAY):
            mst = MailServerType(MailServerType.RELAY)
        else:
            mail_server_type = str(MailServerType.NONE)
            mst = MailServerType(MailServerType.NONE)
        data = {'config': [mst.default()]}

        parts = scfg.from_email.rsplit(" ", 1)
        if len(parts) == 2:
            data['alert-email-name'] = parts[0]
            del parts[0]
        else:
            data['alert-email-name'] = ""

        table = dict.fromkeys(map(ord, '<>'), None)
        data['alert-email-address'] = parts[0].translate(table)

        data['smtp-server'] = scfg.mail_smtp_server
        data['smtp-port'] = scfg.mail_smtp_port
        _ = req.system.getint(scfg.MAIL_SMTP_PORT, default=None)
        if not _ is None:
            data['smtp-port'] = _
        data['smtp-username'] = scfg.mail_username
        _ = req.system.get(scfg.MAIL_USERNAME, default=None)
        if not _ is None:
            data['smtp-username'] = _

        return data

    @required_parameters('action', 'mail-server-type')
    def service_POST(self, req, initial_page=False):
        # Validation of POST data is done by the service.
        action = req.params_get('action')
        if action == 'test':
            # Sanity check
            test_email_recipient = req.params_get('test-email-recipient').\
                                                  strip()
            if test_email_recipient.count(' ') or \
                                          test_email_recipient.find('@') == -1:
                return {'status': 'FAIL'}

        if action == 'test' and initial_page:
            # If 'Test Email' from the initial page, we have to
            # configure postfix and save the config to the system table.
            data = super(SetupMailApplication, self).service(req)
            if 'error' in data:
                return data

            self.commapp.send_cmd('test email ' + test_email_recipient)
            return {'status': 'OK'}

        if action == 'save':
            return super(SetupMailApplication, self).service(req)
        elif action == 'test':
            self.commapp.send_cmd('test email ' + test_email_recipient)
            return {'status': 'OK'}
        else:
            raise exc.HTTPBadRequest(req)

    def service(self, req):
        if req.method == 'GET':
            return self.service_GET(req)
        elif req.method == 'POST':
            return self.service_POST(req)
        else:
            raise exc.HTTPMethodNotAllowed()

class SetupMailTestApplication(BaseSetupApplication):

    def service_POST(self, req):
        test_email_recipient = req.params_get('test-email-recipient').strip()
        # Sanity check
        if test_email_recipient.count(' ') or \
                                      test_email_recipient.find('@') == -1:
            return {'status': 'FAIL'}
        self.commapp.send_cmd('test email ' + test_email_recipient)
        return {'status': 'OK'}


class SetupSSLApplication(JSONProxy):
    """Handler for the 'SERVER SSL CERTIFICATE' section."""

    def __init__(self):
        super(SetupSSLApplication, self).__init__('http://localhost:9092', \
                                    allowed_request_methods=('GET', 'POST'))

    def postprocess(self, req, data):
        return data

    @required_role(Role.MANAGER_ADMIN)
    def service(self, req):
        if req.method == 'GET':
            return self.service_GET(req)
        elif req.method == 'POST':
            return self.service_POST(req)
        else:
            raise exc.HTTPMethodNotAllowed()

    def service_GET(self, req):
        # pylint: disable=unused-argument
        return {}

    def service_POST(self, req):
#        dump(req)
        if req.POST['enable-ssl'] == 'false':
            return {'status': 'OK'}

        # Validation of required parameters is done by the service
        return super(SetupSSLApplication, self).service(req)


class SetupTimezoneApplication(JSONProxy):
    """Handler for the timezone configuration section."""

    def __init__(self):
        super(SetupTimezoneApplication, self).__init__(
            'http://localhost:9093', allowed_request_methods=('GET', 'POST'))

    @required_role(Role.MANAGER_ADMIN)
    def service(self, req):
        return super(SetupTimezoneApplication, self).super(req)

    def postprocess(self, req, data):
        if 'error' in data:
            return data

        if not 'timezone' in data or not data['timezone']:
            return {'error': 'post process missing timezone'}

        req.system.save(SystemConfig.TIMEZONE, data['timezone'])
        return data

    def service_GET(self, req):
        # pylint: disable=unused-argument
        options = OrderedDict({})
        for timezone in timezones:
            options[timezone] = timezone

        scfg = SystemConfig(req.system)
        tzconfig = DictOption('timezone', scfg.timezone, options)
        data = {'config': [tzconfig.default()]}
        return data

    def service_POST(self, req):
        if req.params['timezone'] is None:
            raise exc.HTTPBadRequest()
        return super(SetupTimezoneApplication, self).service(req)

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

        data = {'config': [atype.default()]}
        return data

    def service_POST(self, req):
        authtype = req.params_getint('authentication-type')
        if authtype == None:
            raise exc.HTTPBadRequest()
        req.system.save(SystemConfig.AUTHENTICATION_TYPE, authtype)
        return {'authentication-type': authtype}

class _SetupApplication(BaseSetupApplication):
    """Handler for initial page GET requests."""
    # pylint: disable=too-many-instance-attributes

    def __init__(self):
        super(_SetupApplication, self).__init__()
        self.admin = SetupAdminApplication()
        self.readonly = SetupReadOnlyApplication()
        self.mail = SetupMailApplication()
        self.ssl = SetupSSLApplication()
        self.auth = SetupAuthApplication()
        self.url = SetupURLApplication()
        self.tableau_url = SetupTableauURLApplication()
        self.timezone = SetupTimezoneApplication()

    def service_GET(self, req):
        data = {}
        extend(data, self.admin.service_GET(req))
        extend(data, self.readonly.service_GET(req))
        extend(data, self.mail.service_GET(req))
        extend(data, self.ssl.service_GET(req))
        extend(data, self.auth.service_GET(req))
        extend(data, self.url.service_GET(req))
        extend(data, self.tableau_url.service_GET(req))
        extend(data, self.timezone.service_GET(req))
        return data

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
        self.add_route(r'/readonly\Z', SetupReadOnlyApplication())
        self.add_route(r'/url\Z', SetupURLApplication())
        self.add_route(r'/tableau-url\Z', SetupTableauURLApplication())
        self.add_route(r'/tz\Z', SetupTimezoneApplication())
