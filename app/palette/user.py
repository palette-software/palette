from akiri.framework.ext.sqlalchemy import meta

from controller.profile import UserProfile
from page import PalettePage
from rest import PaletteRESTHandler

class UserApplication(PaletteRESTHandler):
    NAME = 'users'

    def handle(self, req):
        exclude = ['hashed_password', 'salt']
        L = meta.Session.query(UserProfile).all()
        return {'users': [x.todict(pretty=True, exclude=exclude) for x in L]}

class UserConfig(PalettePage):
    TEMPLATE = "user.mako"
    active = 'users'
    expanded = True

def make_users(global_conf):
    return UserConfig(global_conf)
