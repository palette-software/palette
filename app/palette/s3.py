from sqlalchemy.orm.exc import NoResultFound

from akiri.framework.ext.sqlalchemy import meta
from page import PalettePage
from rest import PaletteRESTHandler, required_parameters, required_role

from controller.profile import Role
from controller.s3 import S3

__all__ = ["S3Application"]

ENVID = 1
CONFIG_NAME = 'default'

class S3Application(PaletteRESTHandler):
    NAME = 's3'

    def __init__(self, global_conf):
        super(S3Application, self).__init__(global_conf)

    def insert_or_update(self, envid, name, key, value):
        try:
            entry = meta.Session.query(S3).\
                filter(S3.envid == envid).\
                filter(S3.name == name).one()
        except NoResultFound, e:
            entry = None

        if entry is None:
            entry = S3(envid = envid)
            entry.name = name
            meta.Session.add(entry)

        if key == 'access-key':
            entry.access_key = value
        elif key == 'access-secret':
            entry.secret = value
        elif key == 'bucket-name':
             entry.bucket = value

        meta.Session.commit()

    @classmethod
    def get(self):
        row = S3.get_by_envid_name(ENVID, CONFIG_NAME)
        if row is None:
            return {'access-key': '', 'access-secret': '', 'bucket-name': ''}

        return {'access-key': row.access_key, 'access-secret': row.secret, 'bucket-name': row.bucket}

    def handle_post_access_key(self, req):
        v = req.POST['value']
        self.insert_or_update(ENVID, CONFIG_NAME, 'access-key', v)
        return {'value':v}

    def handle_post_access_secret(self, req):
        v = req.POST['value']
        self.insert_or_update(ENVID, CONFIG_NAME, 'access-secret', v)
        return {'value':v}

    def handle_post_bucket_name(self, req):
        v = req.POST['value']
        self.insert_or_update(ENVID, CONFIG_NAME, 'bucket-name', v)
        return {'value':v}

    def handle_post(self, req):
        path_info = self.base_path_info(req)
        if path_info == 'access-key':
            return self.handle_post_access_key(req)
        elif path_info == 'access-secret':
            return self.handle_post_access_secret(req)
        elif path_info == 'bucket-name':
            return self.handle_post_bucket_name(req)
        else:
            raise exc.HTTPMethodNotAllowed()          

    def handle(self, req):
        if req.method == 'GET':
            return self.get()
        if req.method == 'POST':
            return self.handle_post(req)
        else:
            raise exc.HTTPBadRequest()

class S3Page(PalettePage):
    TEMPLATE = 's3.mako'
    active = 's3'
    integration = True
    required_role = Role.MANAGER_ADMIN

    def __init__(self, global_conf):
        super(S3Page, self).__init__(global_conf)

    def render(self, req, obj=None):
        self.config = S3Application.get()
        return super(S3Page, self).render(req, obj=obj)

def make_s3(global_conf):
    return S3Page(global_conf)
