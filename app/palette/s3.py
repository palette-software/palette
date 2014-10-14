import urlparse
from webob import exc

# pylint: disable=import-error,no-name-in-module
from akiri.framework.ext.sqlalchemy import meta
# pylint: enable=import-error,no-name-in-module

from page import PalettePage
from rest import PaletteRESTHandler, required_parameters

from controller.profile import Role
from controller.cloud import CloudManager, CloudEntry, S3_ID

__all__ = ["S3Application"]

DEFAULT_NAME = 'default'

class S3Application(PaletteRESTHandler):
    NAME = 's3'

    def __init__(self, global_conf):
        super(S3Application, self).__init__(global_conf)

    def _get_cloudid(self, req):
        s3id = req.system.getint(S3_ID, cleanup=True, default=None)
        if s3id is None:
            return None
        return s3id

    def _get(self, req):
        cloudid = self._get_cloudid(req)
        if cloudid is None:
            return None
        return CloudEntry.get_by_envid_cloudid(req.envid, cloudid)

    def _get_by_name(self, envid, name):
        entry = CloudEntry.get_by_envid_name(envid, name,
                                             CloudManager.CLOUD_TYPE_S3)
        if entry is None:
            entry = CloudEntry(envid=envid,
                               cloud_type=CloudManager.CLOUD_TYPE_S3)
            # The name and the bucket are currently the same.
            entry.name = name
            entry.bucket = name
            meta.Session.add(entry)
        return entry

    def _bucket_from_url(self, url):
        if not url.lower().startswith('s3://'):
            # raw bucket name
            return url
        tokens = urlparse.urlparse(url)
        return tokens.netloc

    def _todict(self, entry):
        data = entry.todict(pretty=True)
        data['secret-key'] = data['secret']
        del data['secret']
        data['url'] = 's3://' + data['bucket']
        return data

    def handle_GET(self, req):
        entry = self._get(req)
        if entry is None:
            return {}
        return self._todict(entry)

    @required_parameters('access-key', 'secret-key', 'url')
    def handle_save_POST(self, req):
        # pylint: disable=invalid-name
        bucket = self._bucket_from_url(req.POST['url'])
        if not bucket:
            raise exc.HTTPBadRequest()

        session = meta.Session()

        entry = self._get_by_name(req.envid, bucket)
        entry.access_key = req.POST['access-key']
        entry.secret = req.POST['secret-key']
        session.commit()

        req.system.save(S3_ID, entry.cloudid)
        session.commit()

        return self._todict(entry)

    @required_parameters('action')
    def handle_delete_POST(self, req):
        # pylint: disable=invalid-name
        # 'action' is just sanity check, its not used.
        req.system.delete(S3_ID)
        meta.Session().commit()
        return {}

    def handle(self, req):
        path_info = self.base_path_info(req)
        if req.method == 'GET':
            return self.handle_GET(req)
        elif req.method == 'POST':
            if path_info == 'save':
                return self.handle_save_POST(req)
            elif path_info == 'delete':
                return self.handle_delete_POST(req)
        raise exc.HTTPBadRequest()

class S3Page(PalettePage):
    TEMPLATE = 's3.mako'
    active = 's3'
    integration = True
    required_role = Role.MANAGER_ADMIN

def make_s3(global_conf):
    return S3Page(global_conf)
