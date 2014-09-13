from webob import exc

# pylint: disable=import-error,no-name-in-module
from akiri.framework.ext.sqlalchemy import meta
# pylint: enable=import-error,no-name-in-module

from page import PalettePage, FAKEPW
from rest import PaletteRESTHandler, required_parameters

from controller.profile import Role
from controller.cloud import CloudManager, CloudEntry

__all__ = ["S3Application"]

DEFAULT_NAME = 'default'

class S3Application(PaletteRESTHandler):
    NAME = 's3'

    def __init__(self, global_conf):
        super(S3Application, self).__init__(global_conf)

    def get(self, envid):
        entry = CloudManager.get_by_envid_name(envid, DEFAULT_NAME,
                                               CloudManager.CLOUD_TYPE_S3)
        if entry is None:
            entry = CloudEntry(envid=envid,
                              cloud_type=CloudManager.CLOUD_TYPE_S3)

            entry.name = DEFAULT_NAME
            meta.Session.add(entry)
            meta.Session.commit()
        return entry

    def handle_GET(self, req):
        entry = self.get(req.envid)
        d = entry.todict(pretty=True)
        d['secret'] = entry.secret and FAKEPW or ''
        return d

    @required_parameters('value')
    # pylint: disable=invalid-name
    def handle_access_key_POST(self, req):
        v = req.POST['value']
        entry = self.get(req.envid)
        entry.access_key = v
        meta.Session.commit()
        return {'value':v}

    @required_parameters('value')
    # pylint: disable=invalid-name
    def handle_secret_POST(self, req):
        value = req.POST['value']
        entry = self.get(req.envid)
        entry.secret = value
        meta.Session.commit()
        retval = value and FAKEPW or ''
        return {'value':retval}

    @required_parameters('value')
    # pylint: disable=invalid-name
    def handle_bucket_POST(self, req):
        value = req.POST['value']
        if value.find('s3://') == 0:
            value = value[5:]
        elif value.find('https://s3.amazonaws.com/') == 0:
            value = value[25:]
        entry = self.get(req.envid)
        entry.bucket = value
        meta.Session.commit()
        return {'value':value}

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
            return self.handle_GET(req)
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
        # pylint: disable=attribute-defined-outside-init
        entry = CloudManager.get_by_envid_name(req.envid, DEFAULT_NAME,
                                               CloudManager.CLOUD_TYPE_S3)
        if entry is None:
            entry = CloudEntry(envid=req.envid,
                               cloud_type=CloudManager.CLOUD_TYPE_S3)
            entry.name = DEFAULT_NAME
        self.access_key = entry.access_key and entry.access_key or ''
        self.secret = entry.secret and FAKEPW or ''
        self.bucket = entry.bucket and entry.bucket or ''
        return super(S3Page, self).render(req, obj=obj)

def make_s3(global_conf):
    return S3Page(global_conf)
