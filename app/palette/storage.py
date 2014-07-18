from webob import exc

from akiri.framework.ext.sqlalchemy import meta
from akiri.framework.config import store

from controller.profile import UserProfile, Role, Publisher, Admin, License
from controller.auth import AuthManager
from controller.util import DATEFMT
from controller.system import SystemEntry

from page import PalettePage
from rest import PaletteRESTHandler, required_parameters, required_role

class StoragePage(PalettePage):
    TEMPLATE = "storage.mako"
    active = 'storage'
    expanded = True
    required_role = Role.READONLY_ADMIN
    
    def __init__(self, global_conf):
        super(StoragePage, self).__init__(global_conf)       
        #query = meta.Session.query(SystemEntry)
        #print query

    def render(self, req, obj=None):        
        return super(StoragePage, self).render(req, obj=obj)

def make_storage(global_conf):
    return StoragePage(global_conf)
