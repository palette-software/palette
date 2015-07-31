import apt

class PackageException(StandardError):
    pass

class Package(object):

    @classmethod
    def apt_get_update(cls):
        cache = apt.Cache()
        try:
            cache.update()
        except (apt.cache.LockFailedException,
                apt.cache.FetchFailedException) as ex:
            raise PackageException(str(ex))

        cache.open(None)
        return Package.get(cache)

    @classmethod
    def list_packages(cls):
        return Package.get(apt.Cache())

    @classmethod
    def get(cls, cache=None):
        """Returns a dictionary with the 'controller' and 'palette'
           package information if they are installed.
           Can raise exceptions:
                PackageException
        """

        if not cache:
            cache = apt.Cache()

        packages = {}
        if 'controller' in cache:
            packages['controller'] = cache['controller']
        if 'palette' in cache:
            packages['palette'] = cache['palette']

        return packages
