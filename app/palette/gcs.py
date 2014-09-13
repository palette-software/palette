from webob import exc

# pylint: disable=import-error,no-name-in-module
from akiri.framework.ext.sqlalchemy import meta
# pylint: enable=import-error,no-name-in-module

from page import PalettePage, FAKEPW
from rest import PaletteRESTHandler, required_parameters

from controller.profile import Role
from controller.cloud import CloudManager, CloudEntry

__all__ = ["GCSApplication"]

DEFAULT_NAME = 'default'

class GCSApplication(PaletteRESTHandler):
    NAME = 'gcs'

    def __init__(self, global_conf):
        super(GCSApplication, self).__init__(global_conf)

    def get(self, envid):
        entry = CloudManager.get_by_envid_name(envid, DEFAULT_NAME,
                                               CloudManager.CLOUD_TYPE_GCS)
        if entry is None:
            entry = CloudEntry(envid=envid,
                               cloud_type=CloudManager.CLOUD_TYPE_GCS)
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
        value = req.POST['value']
        entry = self.get(req.envid)
        entry.access_key = value
        meta.Session.commit()
        return {'value':value}

    @required_parameters('value')
    # pylint: disable=invalid-name
    def handle_secret_POST(self, req):
        value = req.POST['value']
        entry = self.get(req.envid)
        entry.secret = value
        meta.Session.commit()
        value = value and FAKEPW or ''
        return {'value':value}

    @required_parameters('value')
    # pylint: disable=invalid-name
    def handle_bucket_POST(self, req):
        value = req.POST['value']
        if value.find('gs://') == 0:
            value = value[5:]
        elif value.find('https://storage.googleapis.com/') == 0:
            value = value[31:]
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

class GCSPage(PalettePage):
    TEMPLATE = 'gcs.mako'
    active = 'gcs'
    integration = True
    required_role = Role.MANAGER_ADMIN

    def render(self, req, obj=None):
        # pylint: disable=attribute-defined-outside-init
        entry = CloudManager.get_by_envid_name(req.envid, DEFAULT_NAME,
                                               CloudManager.CLOUD_TYPE_GCS)
        if entry is None:
            entry = CloudEntry(envid=req.envid,
                               cloud_type=CloudManager.CLOUD_TYPE_GCS)
            entry.name = DEFAULT_NAME
        self.access_key = entry.access_key and entry.access_key or ''
        self.secret = entry.secret and FAKEPW or ''
        self.bucket = entry.bucket and entry.bucket or ''
        return super(GCSPage, self).render(req, obj=obj)

def make_gcs(global_conf):
    return GCSPage(global_conf)
