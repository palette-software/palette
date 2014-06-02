from webob import exc

from akiri.framework.ext.sqlalchemy import meta

from controller.profile import UserProfile, Role
from page import PalettePage
from rest import PaletteRESTHandler

class UserApplication(PaletteRESTHandler):
    NAME = 'users'

    def admin_levels(self):
        L = meta.Session.query(Role).all()
        return [{'name': x.name, 'id': x.roleid} for x in L]

    def users(self):
        q = meta.Session.query(UserProfile)
        return q.order_by(UserProfile.friendly_name.asc()).all()
        
    def handle(self, req):
        path_info = self.base_path_info(req)
        if path_info == '':
            if req.method != 'GET':
                raise exc.HTTPMethodNotAllowed()
            return self.handle_GET(req)
        if path_info == 'admin':
            return self.handle_admin(req);
        raise exc.HTTPNotFound()

    def handle_GET(self, req):
        exclude = ['hashed_password', 'salt']
        users = []
        for user in self.users():
            d = user.todict(pretty=True, exclude=exclude)
            d['admin-type'] = user.role.name;
            users.append(d)
        return {'users': users, 'admin-levels': self.admin_levels()}

    def handle_admin(self, req):
        if req.method != 'POST':
            raise exc.HTTPMethodNotAllowed()
        if 'userid' not in req.POST or 'roleid' not in req.POST:
            raise exc.HTTPBadRequest()
        user = UserProfile.get(int(req.POST['userid']))
        if not user:
            raise exc.HTTPGone()
        user.roleid = int(req.POST['roleid'])
        meta.Session.commit()
        return {}

class UserConfig(PalettePage):
    TEMPLATE = "user.mako"
    active = 'users'
    expanded = True

def make_users(global_conf):
    return UserConfig(global_conf)
