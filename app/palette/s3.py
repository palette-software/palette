from webob import exc
from sqlalchemy.orm.exc import NoResultFound

from akiri.framework.ext.sqlalchemy import meta
from page import PalettePage
from rest import PaletteRESTHandler, required_parameters, required_role

from controller.profile import Role
from controller.s3 import S3

from controller.environment import Environment

__all__ = ["S3Application"]

DEFAULT_NAME = 'default'

class S3Application(PaletteRESTHandler):
    NAME = 's3'

    def __init__(self, global_conf):
        super(S3Application, self).__init__(global_conf)

    def get(self):
        entry = S3.get_by_envid_name(self.envid, DEFAULT_NAME)
        if entry is None:
            entry = S3(envid = self.envid)
            entry.name = DEFAULT_NAME
            meta.Session.add(entry)
            meta.Session.commit()
        return entry

    def handle_GET(self):
        entry = self.get()
        d = entry.todict(pretty=True)
        d['secret'] =  entry.secret and '********' or ''
        return d

    @required_parameters('value')
    def handle_access_key_POST(self, req):
        v = req.POST['value']
        entry = self.get()
        entry.access_key = v
        meta.Session.commit()
        return {'value':v}

    @required_parameters('value')
    def handle_secret_POST(self, req):
        v = req.POST['value']
        entry = self.get()
        entry.secret = v
        meta.Session.commit()
        value = v and '********' or ''
        return {'value':v}

    @required_parameters('value')
    def handle_bucket_POST(self, req):
        v = req.POST['value']
        entry = self.get()
        entry.bucket = v
        meta.Session.commit()
        return {'value':v}

    @required_parameters('value')
    def handle_POST(self, req):
        path_info = self.base_path_info(req)
        if path_info == 'access-key':
            return self.handle_access_key_POST(req)
        elif path_info == 'secret':
            return self.handle_secret_POST(req)
        elif path_info == 'bucket':
            return self.handle_bucket_POST(req)
        else:
            raise exc.HTTPBadRequest()

    def handle(self, req):
        if req.method == 'GET':
            return self.handle_GET()
        elif req.method == 'POST':
            return self.handle_POST(req)
        else:
            raise exc.HTTPBadRequest()

class S3Page(PalettePage):
    TEMPLATE = 's3.mako'
    active = 's3'
    integration = True
    required_role = Role.MANAGER_ADMIN

    def render(self, req, obj=None):
        envid = Environment.get().envid # FIXME
        entry = S3.get_by_envid_name(envid, DEFAULT_NAME)
        if entry is None:
            entry = S3(envid = envid)
            entry.name = DEFAULT_NAME
        self.access_key = entry.access_key and entry.access_key or ''
        self.secret = entry.secret and '********' or ''
        self.bucket = entry.bucket and entry.bucket or ''
        return super(S3Page, self).render(req, obj=obj)

def make_s3(global_conf):
    return S3Page(global_conf)
