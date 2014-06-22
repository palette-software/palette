import calendar
from webob import exc

from akiri.framework.ext.sqlalchemy import meta
from akiri.framework.config import store

from controller.profile import UserProfile, Role, Publisher, Admin, License
from controller.auth import AuthManager
from controller.util import DATEFMT

from page import PalettePage
from rest import PaletteRESTHandler, required_parameters, required_role

class UserApplication(PaletteRESTHandler):
    NAME = 'users'

    def admin_levels(self):
        L = meta.Session.query(Role).all()
        return [{'name': x.name, 'id': x.roleid} for x in L]

    def users(self):
        q = meta.Session.query(UserProfile)
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
        publisher_tristate = d['publisher-tristate']
        info = 'Tableau '
        if publisher_tristate == Publisher.IMPLICIT or \
                publisher_tristate == Publisher.GRANTED:
            info += 'Publisher & '
        info += Admin.str(user_admin_level, system_admin_level)
        return info

    def license_info(self, d):
        if 'licensing-role-id' not in d:
            return 'Unknown'
        return License.str(d['licensing-role-id'])

    def last_user_import(self):
        try:
            entry = self.system.entry(AuthManager.LAST_IMPORT_KEY)
            return entry.modification_time.strftime(DATEFMT)
        except ValueError:
            return 'never'

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
        raise exc.HTTPNotFound()

    def handle_GET(self, req):
        exclude = ['hashed_password', 'salt']
        users = []
        for user in self.users():
            d = user.todict(pretty=True, exclude=exclude)
            d['admin-type'] = user.role.name;
            d['visited-info'] = self.visited_info(d)
            d['tableau-info'] = self.tableau_info(d)
            d['license-info'] = self.license_info(d)
            if 'login-at' not in d:
                d['login-at'] = user.name == 'palette' and 'N/A' or 'never'

            users.append(d)
        return {'users': users,
                'admin-levels': self.admin_levels(),
                'last-update': self.last_user_import()}

    # refresh request
    @required_role(Role.MANAGER_ADMIN)
    @required_parameters('action')
    def handle_POST(self, req):
        if req.POST['action'].lower() != 'refresh':
            raise exc.HTTPBadRequest()
        try:
            self.telnet.send_cmd('auth import', sync=True)
        except RuntimeError:
            pass
        return self.handle_GET(req)

    @required_role(Role.SUPER_ADMIN)
    @required_parameters('userid', 'roleid')
    def handle_admin(self, req):
        if req.method != 'POST':
            raise exc.HTTPMethodNotAllowed()
        user = UserProfile.get(int(req.POST['userid']))
        if not user:
            raise exc.HTTPGone()
        user.roleid = int(req.POST['roleid'])
        meta.Session.commit()
        return {}

    @required_role(Role.MANAGER_ADMIN)
    @required_parameters('name', 'value')
    def handle_email(self, req):
        if req.method != 'POST':
            raise exc.HTTPMethodNotAllowed()
        # FIXME: test authorization
        profile = UserProfile.get_by_name(req.POST['name'])
        profile.email = req.POST['value']
        meta.Session.commit()
        return {}

class UserConfig(PalettePage):
    TEMPLATE = "user.mako"
    active = 'users'
    expanded = True
    required_role = Role.READONLY_ADMIN

def make_users(global_conf):
    return UserConfig(global_conf)
