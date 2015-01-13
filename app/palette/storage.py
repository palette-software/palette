from controller.profile import Role
from .rest import required_role, PaletteRESTApplication

class StorageApplication(PaletteRESTApplication):

    @required_role(Role.MANAGER_ADMIN)
    def service(self, req):
        # none, s3, gcs, local
        return {'storage-type': 'none'}
