from webob import exc
from sqlalchemy import func
import akiri.framework.sqlalchemy as meta

from controller.profile import UserProfile, Role, Admin, License
from controller.util import str2bool, LETTERS
from controller.system import SystemKeys

from .page import PalettePage
from .rest import required_parameters, required_role, PaletteRESTApplication

class UserApplication(PaletteRESTApplication):
    # pylint: disable=too-many-public-methods

    def admin_levels(self):
        roles = meta.Session.query(Role).all()
        options = [{'item': x.name, 'id': x.roleid} for x in roles]
        return {'options': options}

    def alpha_count(self, envid):
        data = {}
        connection = meta.get_connection()

        stmt = \
            "SELECT UPPER(SUBSTR(friendly_name, 1, 1)) AS alpha, " +\
            "       COUNT(*) AS count FROM users " +\
            "WHERE envid = " + str(envid) + " AND userid > 0 " +\
            "GROUP BY UPPER(SUBSTR(friendly_name, 1, 1))"

        total = 0
        for row in connection.execute(stmt):
            count = int(row['count'])
            if count == 0:
                continue
            data[row['alpha']] = count
            total += count
        data['__total__'] = total
        return data

    def users(self, envid, startswith=None):
        query = meta.Session.query(UserProfile).\
            filter(UserProfile.envid == envid).\
            filter(UserProfile.userid > 0)
        if startswith:
            regex = startswith.upper() + '%'
            query = query.filter(\
                func.upper(UserProfile.friendly_name).like(regex))
        return query.order_by(UserProfile.friendly_name.asc()).all()

    def visited_info(self, d):
        if not 'timestamp' in d or not d['timestamp']:
            return 'Never logged in'
        return 'Last Visited at ' + d['timestamp']

    def tableau_info(self, d):
        if d['name'] == 'palette':
            return 'Palette System User'
        if 'system-admin-level' in d:
            system_admin_level = d['system-admin-level']
        else:
            system_admin_level = 0
        if 'user-admin-level' in d:
            user_admin_level = d['user-admin-level']
        else:
            user_admin_level = 0
        info = 'Tableau '
        if 'publisher' in d and d['publisher']:
            info += 'Publisher & '
        info += Admin.str(user_admin_level, system_admin_level)
        return info

    def license_info(self, d):
        if 'licensing-role-id' not in d:
            return 'Unknown'
        return License.str(d['licensing-role-id'])

    def service(self, req):
        if 'action' in req.environ:
            action = req.environ['action']
            if action == 'admin':
                return self.handle_admin(req)
            elif action == 'email-level':
                return self.handle_email_level(req)
            raise exc.HTTPNotFound()

        if req.method == 'GET':
            return self.handle_GET(req)
        elif req.method == 'POST':
            return self.handle_POST(req)
        raise exc.HTTPMethodNotAllowed()

    def first_populated_letter(self, counts):
        for letter in LETTERS:
            if letter in counts and counts[letter] > 0:
                return letter
        return None

    def handle_GET(self, req):
        counts = self.alpha_count(req.envid)

        startswith = None
        if 'startswith' in req.GET:
            startswith = req.GET['startswith']
        else:
            # estimated: < 10K
            count = counts['__total__']
            if count > 25:
                startswith = self.first_populated_letter(counts)

        users = []
        for user in self.users(req.envid, startswith=startswith):
            d = user.todict(pretty=True, exclude=['hashed_password', 'salt'])
            d['admin-type'] = user.role.name # FIXME
            d['visited-info'] = self.visited_info(d)
            d['tableau-info'] = self.tableau_info(d) # FIXME
            d['license-info'] = self.license_info(d)
            d['palette-display-role'] = user.display_role()
            if 'login-at' not in d:
                d['login-at'] = user.name == 'palette' and 'N/A' or 'never'
            d['current'] = (req.remote_user.userid == user.userid)

            users.append(d)
        data = {'users': users,
                'admin-levels': self.admin_levels(),
                'counts': counts
        }

        last_update = req.system[SystemKeys.AUTH_TIMESTAMP]
        if not last_update is None:
            data['last-update'] = last_update

        return data

    # refresh request
    @required_role(Role.MANAGER_ADMIN)
    @required_parameters('action')
    def handle_POST(self, req):
        if req.POST['action'].lower() != 'refresh':
            raise exc.HTTPBadRequest()
        try:
            self.commapp.send_cmd('auth import', req=req, read_response=True)
        except RuntimeError:
            pass
        return self.handle_GET(req)

    @required_role(Role.SUPER_ADMIN)
    @required_parameters('userid', 'id')
    def handle_admin(self, req):
        user = UserProfile.get(req.envid, int(req.POST['userid']))
        if not user:
            raise exc.HTTPGone()
        roleid = int(req.POST['id'])
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

    # FIXME: unused, remove.
    @required_role(Role.MANAGER_ADMIN)
    def handle_email_other(self, req):
        return self.set_email(req, req.POST['name'], req.POST['value'])

    # FIXME: unused, remove.
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

class UserConfigPage(PalettePage):
    TEMPLATE = "user.mako"
    active = 'users'
    expanded = True
    required_role = Role.READONLY_ADMIN
