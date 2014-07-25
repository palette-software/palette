from akiri.framework.config import store
from akiri.framework.ext.sqlalchemy import meta

from controller.domain import Domain

from page import PalettePage
from rest import PaletteRESTHandler, required_parameters, required_role

from controller.profile import UserProfile, Role, Publisher, Admin, License
from controller.s3 import S3

__all__ = ["S3Application"]

class S3Application(PaletteRESTHandler):
    NAME = 's3'

    def __init__(self, global_conf):
        super(S3Application, self).__init__(global_conf)
        self.ENVID = 1
        self.CONFIG_NAME = 'default'

    def handle_get(self, req):
        row = S3.get_by_envid_name(self.ENVID, self.CONFIG_NAME)
        if row is None:
            return {'access-key-id': '', 'access-key-secret': '', 'bucket-name': ''}

        return {'access-key-id': row.access_key, 'access-key-secret': row.secret, 'bucket-name': row.bucket}

    @required_role(Role.MANAGER_ADMIN)
    @required_parameters('name', 'value')
    def handle_post(self, req):
        k = req.POST['name']
        v = req.POST['value']
        S3.insert_or_update(self.ENVID, self.CONFIG_NAME, k, v)
        return {}

    def handle(self, req):
        if req.method == "GET":
            return self.handle_get(req)
        if req.method == "POST":
            return self.handle_post(req)
        else:
            raise exc.HTTPBadRequest()

class S3Page(PalettePage):
    TEMPLATE = 's3.mako'
    active = 's3'
    expanded = True
    integration = True
    required_role = Role.MANAGER_ADMIN

def make_s3(global_conf):
    return S3Page(global_conf)
