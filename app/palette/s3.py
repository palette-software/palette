from webob import exc

# pylint: disable=import-error,no-name-in-module
from akiri.framework.ext.sqlalchemy import meta
# pylint: enable=import-error,no-name-in-module

from page import PalettePage
from rest import PaletteRESTHandler, required_parameters

from controller.profile import Role
from controller.cloud import CloudManager, CloudEntry

__all__ = ["S3Application"]

DEFAULT_NAME = 'default'

class S3Application(PaletteRESTHandler):
    NAME = 's3'

    def __init__(self, global_conf):
        super(S3Application, self).__init__(global_conf)

    def _get(self, envid):
        return CloudEntry.get_by_envid_type(envid, CloudManager.CLOUD_TYPE_S3)

    def _get_by_bucket(self, envid, bucket):
        entry = CloudEntry.get_by_envid_name(envid, bucket,
                                             CloudManager.CLOUD_TYPE_S3)
        if entry is None:
            entry = CloudEntry(envid=envid,
                               cloud_type=CloudManager.CLOUD_TYPE_S3)
            entry.bucket = bucket
            entry.name = bucket
            meta.Session.add(entry)
            meta.Session.commit()
        return entry

    def handle_GET(self, req):
        entry = self._get(req.envid)
        if entry is None:
            return {}
        return entry.todict(pretty=True)

    @required_parameters('access-key', 'secret-key', 'bucket')
    def handle_POST(self, req):
        path_info = self.base_path_info(req)
        if path_info != '':
            raise exc.HTTPBadRequest()

        entry = self._get_by_bucket(req.envid, req.POST['bucket'])
        entry.access_key = req.POST['access-key']
        entry.secret = req.POST['secret-key']
        meta.Session.commit()
        return entry.todict(pretty=True)

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

def make_s3(global_conf):
    return S3Page(global_conf)
