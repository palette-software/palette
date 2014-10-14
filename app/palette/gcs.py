from controller.profile import Role
from controller.cloud import CloudManager, GCS_ID

from cloud import CloudHandler
from page import PalettePage

__all__ = ["GCSApplication"]

class GCSApplication(CloudHandler):
    NAME = 'gcs'

    @property
    def KEY(self):
        return GCS_ID

    @property
    def TYPE(self):
        return CloudManager.CLOUD_TYPE_GCS

    def url_to_bucket(self, url):
        value = url.lower()
        if value.startswith('gs://'):
            return url[5:]
        elif value.startswith('https://storage.googleapis.com/'):
            return url[31:]
        # raw bucket
        return url

    def bucket_to_url(self, bucket):
        return 'gs://' + bucket

class GCSPage(PalettePage):
    TEMPLATE = 'gcs.mako'
    active = 'gcs'
    integration = True
    required_role = Role.MANAGER_ADMIN

def make_gcs(global_conf):
    return GCSPage(global_conf)
