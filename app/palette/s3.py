from controller.profile import Role
from controller.cloud import CloudManager, S3_ID

from .cloud import CloudApplication
from .page import PalettePage

__all__ = ["S3Application"]

class S3Application(CloudApplication):

    NAME = 's3'

    @property
    def KEY(self):
        return S3_ID

    @property
    def TYPE(self):
        return CloudManager.CLOUD_TYPE_S3

    def url_to_bucket(self, url):
        value = url.lower()
        if value.startswith('s3://'):
            return url[5:]
        elif value.startswith('https://s3.amazonaws.com/'):
            return url[25:]
        # raw bucket name
        return url

    def bucket_to_url(self, bucket):
        return 's3://' + bucket


class S3Page(PalettePage):
    TEMPLATE = 's3.mako'
    active = 's3'
    integration = True
    required_role = Role.MANAGER_ADMIN

def make_s3(global_conf):
    return S3Page(global_conf)
