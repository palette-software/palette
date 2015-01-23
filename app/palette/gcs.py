from controller.cloud import CloudManager, GCS_ID

from .cloud import CloudApplication

__all__ = ["GCSApplication"]

class GCSApplication(CloudApplication):

    @property
    def NAME(self):
        return 'gcs'

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
