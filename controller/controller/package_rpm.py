class PackageException(StandardError):
    pass

class Package(object):

    @classmethod
    def apt_get_update(cls):
        raise PackageException("Not available")

    @classmethod
    def list_packages(cls):
        return None

    @classmethod
    # pylint: disable=unused-argument
    def get(cls, cache=None):
        raise PackageException("Not available")
