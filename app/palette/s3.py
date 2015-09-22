from controller.cloud import CloudManager
from controller.system import SystemKeys

from .cloud import CloudApplication

__all__ = ["S3Application"]

class S3Application(CloudApplication):

    @property
    def NAME(self):
        return 's3'

    @property
    def KEY(self):
        return SystemKeys.S3_ID

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
