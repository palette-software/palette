from webob import exc

from akiri.framework.ext.sqlalchemy import meta
from akiri.framework.config import store

from controller.profile import UserProfile, Role, Publisher, Admin, License
from controller.auth import AuthManager
from controller.util import DATEFMT
from controller.system import SystemEntry
from controller.domain import Domain
from controller.workbooks import WorkbookEntry, WorkbookUpdatesEntry

from page import PalettePage
from rest import PaletteRESTHandler, required_parameters, required_role

import json

__all__ = ["StorageApplication"]

class StorageApplication(PaletteRESTHandler):
    NAME = 'storage'

    def __init__(self, global_conf):
        super(StorageApplication, self).__init__(global_conf)

    def handle_get(self, req):
        query = meta.Session.query(SystemEntry).all()

        storage = []
        for entry in query:
            item = {}
            item[entry.key] = entry.value
            storage.append(item)

        return {'storage': storage}

    @required_role(Role.MANAGER_ADMIN)
    @required_parameters('id', 'value')
    def handle_post(self, req):
        key = req.POST['id']
        value = req.POST['value']
        if key == "main_warning":
            pass
        elif key == "main_error":
            pass
        elif key == "other_warning":
            pass
        elif key == "other_error":
            pass        
        return {}

    def handle(self, req):
        if req.method == "GET":
            return self.handle_get(req)
        if req.method == "POST":
            return self.handle_post(req)
        else:
            raise exc.HTTPBadRequest()

class StoragePage(PalettePage):
    TEMPLATE = "storage.mako"
    active = 'storage'
    expanded = True
    required_role = Role.MANAGER_ADMIN

    def handle(self, req):
        return None

def make_storage(global_conf):
    return StoragePage(global_conf)
