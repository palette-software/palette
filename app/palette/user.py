import calendar
from webob import exc

from akiri.framework.ext.sqlalchemy import meta
from akiri.framework.config import store

from controller.profile import UserProfile, Role, Publisher, Admin, License
from controller.auth import AuthManager
from controller.util import str2bool

from page import PalettePage
from rest import PaletteRESTHandler, required_parameters, required_role

class UserApplication(PaletteRESTHandler):
    NAME = 'users'

    def admin_levels(self):
        L = meta.Session.query(Role).all()
        return [{'name': x.name, 'id': x.roleid} for x in L]

    def users(self, envid):
        q = meta.Session.query(UserProfile).\
            filter(UserProfile.envid == envid).\
            filter(UserProfile.userid > 0)
        return q.order_by(UserProfile.friendly_name.asc()).all()
        
    def visited_info(self, d):
        if not 'timestamp' in d or not d['timestamp']:
            return 'Never logged in'
        return 'Last Visited at ' + d['timestamp']

    def tableau_info(self, d):
        if d['name'] == 'palette':
            return 'Palette System User'
        system_admin_level = d['system-admin-level']
        user_admin_level = d['user-admin-level']
        publisher = d['publisher']
        info = 'Tableau '
        if d['publisher']:
            info += 'Publisher & '
        info += Admin.str(user_admin_level, system_admin_level)
        return info

    def license_info(self, d):
        if 'licensing-role-id' not in d:
            return 'Unknown'
        return License.str(d['licensing-role-id'])

    def last_user_import(self, req):
        modtime = req.system.modification_time(AuthManager.LAST_IMPORT_KEY)
        return modtime and modtime or 'never'

    def handle(self, req):
        path_info = self.base_path_info(req)
        if path_info == '':
            if req.method == 'GET':
                return self.handle_GET(req)
            elif req.method == 'POST':
                return self.handle_POST(req)
            raise exc.HTTPMethodNotAllowed()
        if path_info == 'admin':
            return self.handle_admin(req)
        if path_info == 'email':
            return self.handle_email(req)
        if path_info == 'email-level':
            return self.handle_email_level(req)

        raise exc.HTTPNotFound()

    def handle_GET(self, req):
        exclude = ['hashed_password', 'salt']
        users = []
        for user in self.users(req.envid):
            d = user.todict(pretty=True, exclude=exclude)
            d['admin-type'] = user.role.name; # FIXME
            d['visited-info'] = self.visited_info(d)
            d['tableau-info'] = self.tableau_info(d) # FIXME
            d['license-info'] = self.license_info(d)
            if 'login-at' not in d:
                d['login-at'] = user.name == 'palette' and 'N/A' or 'never'

            users.append(d)
        return {'users': users,
                'admin-levels': self.admin_levels(),
                'last-update': self.last_user_import(req)}

    # refresh request
    @required_role(Role.MANAGER_ADMIN)
    @required_parameters('action')
    def handle_POST(self, req):
        if req.POST['action'].lower() != 'refresh':
            raise exc.HTTPBadRequest()
        try:
            self.telnet.send_cmd('auth import', req=req, sync=True)
        except RuntimeError:
            pass
        return self.handle_GET(req)

    @required_role(Role.SUPER_ADMIN)
    @required_parameters('userid', 'roleid')
    def handle_admin(self, req):
        user = UserProfile.get(req.envid, int(req.POST['userid']))
        if not user:
            raise exc.HTTPGone()
        roleid = int(req.POST['roleid'])
        user.roleid = roleid
        meta.Session.commit()
        return {'roleid':roleid}

    def get_profile(self, req, name):
        if name == req.remote_user.name:
            profile = req.remote_user
        else:
            profile = UserProfile.get_by_name(req.envid, name)
        if profile is None:
            raise exc.HTTPNotFound()
        return profile

    def set_email(self, req, name, value):
        profile = self.get_profile(req, name)
        profile.email = value
        meta.Session.commit()
        return {'value':value}

    def set_email_level(self, req, name, value):
        profile = self.get_profile(req, name)
        profile.email_level = value
        meta.Session.commit()
        return {'value':value}

    @required_role(Role.MANAGER_ADMIN)
    def handle_email_other(self, req):
        return self.set_email(req, req.POST['name'], req.POST['value'])

    @required_parameters('name', 'value')
    def handle_email(self, req):
        # any user may update their own email address.
        if req.remote_user.name == req.POST['name']:
            return self.set_email(req, req.remote_user.name, req.POST['value'])
        return self.handle_email_other(req)

    @required_role(Role.MANAGER_ADMIN)
    def handle_email_level_other(self, req, name, value):
        return self.set_email_level(req, name, value)

    @required_parameters('name', 'value')
    def handle_email_level(self, req):
        name = req.POST['name']
        value = int(str2bool(req.POST['value']))

        # any user may update their own email settings.
        if name == req.remote_user.name:
            return self.set_email_level(req, name, value)

        return self.handle_email_level_other(req, name, value)

class UserConfig(PalettePage):
    TEMPLATE = "user.mako"
    active = 'users'
    expanded = True
    required_role = Role.READONLY_ADMIN

def make_users(global_conf):
    return UserConfig(global_conf)
