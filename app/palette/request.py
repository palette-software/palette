""" Helper classes that exist entirely within the Request lifecycle """
# pylint: enable=missing-docstring,relative-import
from webob import exc

from akiri.framework import GenericWSGI
import akiri.framework.sqlalchemy as meta

from controller.domain import Domain
from controller.environment import Environment
from controller.profile import UserProfile
from controller.system import SystemEntry

class System(dict):
    """ Caching container for all system table entries.  The object is created
    and destroyed with the request instance. """
    # pylint: disable=too-many-public-methods
    def __init__(self, req):
        super(System, self).__init__()
        # Technically, req doesn't need to be saved, only envid is used,
        # but this reiterates that the system lifecycle is the same as
        # that of the request.
        self.req = req
        for entry in SystemEntry.get_all(self.req.envid):
            dict.__setitem__(self, entry.key, entry.value)

    def __delitem__(self, key):
        """
        Delete a row from the system table.
        NOTE: The database delete is only done if the key is found
        in the data dict.
        """
        dict.__delitem__(self, key)
        SystemEntry.delete(filters={'envid':self.req.envid, 'key':key})

    def delete(self, key):
        """ Deprecated: instead use the below line directly. """
        del self[key]

    def get(self, key, **kwargs):
        """ Get a value with a default """
        if 'default' in kwargs:
            default = kwargs['default']
            have_default = True
            del kwargs['default']
        else:
            have_default = False

        if not key in self:
            if have_default:
                return default
            raise KeyError('No such key: ' + key)

        return self[key]

    def getint(self, key, **kwargs):
        """ Get the value as an integer, allowing a 'default' value.
        NOTE: if 'cleanup' is specified then 'bad' values are removed from
        the database when found.
        """
        if 'cleanup' in kwargs:
            cleanup = kwargs['cleanup']
            del kwargs['cleanup']
        else:
            cleanup = False

        if 'default' in kwargs:
            default = kwargs['default']
            have_default = True
            del kwargs['default']
        else:
            have_default = False

        try:
            value = int(self[key])
        except KeyError, ex:
            if have_default:
                return default
            raise ex
        except ValueError, ex:
            if cleanup:
                del self[key]
            if have_default:
                return default
            raise ex
        return value

    def getyesno(self, key, **kwargs):
        """ Get a system value that is either 'yes' or 'no', potentially with
        a default value specified.
        NOTE: Allows the 'cleanup' keyword argument (see getint())
        """
        if 'cleanup' in kwargs:
            cleanup = kwargs['cleanup']
            del kwargs['cleanup']
        else:
            cleanup = False

        if 'default' in kwargs:
            default = kwargs['default']
            have_default = True
            del kwargs['default']
        else:
            have_default = False

        try:
            value = self[key].lower()
        except KeyError, ex:
            if have_default:
                return default
            raise ex

        if value == 'no':
            return False
        elif value == 'yes':
            return True

        if cleanup:
            del self[key]

        if have_default:
            return default
        raise ValueError("Bad value for system key '%s': %d" % key, value)

    def __setitem__(self, key, value):
        """ Update the system table but don't do a database commit """
        session = meta.Session()
        if key in self:
            if value == self[key]:
                return
        entry = SystemEntry(envid=self.req.envid, key=key, value=str(value))
        session.add(entry)
        dict.__setitem__(self, key, value)

    def save(self, key, value):
        """ Update the database and commit """
        self[key] = value
        meta.commit()


class Platform(object):
    """ This class determines the type of system currently running,
    specifically this instance determines Pro versus Enterprise. """

    SYSTEM_KEY_PRODUCT = 'platform-product'
    SYSTEM_KEY_IMAGE = 'platform-image'
    SYSTEM_KEY_LOCATION = 'platform-location'

    PRODUCT_PRO = 'pro'
    PRODUCT_ENT = 'enterprise'

    IMAGE_AWS = 'aws'
    IMAGE_VMWARE = 'vmware'

    LOCATION_CUSTOMER = 'customer'
    LOCATION_PALETTE = 'palette'

    def __init__(self, req):
        self.req = req
        # don't reference 'system' until needed.

    @property
    def product(self):
        """ The product running: Pro or Enterprise, default: Enterprise """
        return self.req.system.get(self.SYSTEM_KEY_PRODUCT,
                                   default=self.PRODUCT_ENT)

    @property
    def image(self):
        """ The image type: AWS or VMware, default: VMware """
        return self.req.system.get(self.SYSTEM_KEY_IMAGE,
                                   default=self.IMAGE_VMWARE)

    @property
    def location(self):
        """ Where the image is running: Palette AWS or Customer location,
        default: Customer location"""
        return self.req.system.get(self.SYSTEM_KEY_LOCATION,
                                   default=self.LOCATION_CUSTOMER)

def req_getattr(req, name):
    """ __getattr__ addin for the webob Request object.  This functionality
    is similar to, but runs before,  the AdhocAttrMixin from webob itself."""
    if name == 'envid':
        return req.palette_environment.envid
    if name == 'palette_domain': # webob already has a 'domain' property.
        return Domain.getone()
    if name == 'palette_environment': # to be consistent with palette_domain
        return Environment.get()
    if name == 'system':
        return System(req)
    if name == 'platform':
        return Platform(req)

    raise AttributeError(name)


class BaseMiddleware(GenericWSGI):
    """Do initial setup of the request object."""
    def service(self, req):
        req.getattr = req_getattr


class RemoteUserMiddleware(GenericWSGI):
    """Convert req.remote_user string to UserProfile instance."""
    def service(self, req):
        # req.remote_user can possibly be None if AD authentication works,
        # but there is a problem importing the user database from Tableau.
        if req.remote_user is None:
            # FIXME: print to the error log?
            raise exc.HTTPTemporaryRedirect(location='/login')
        # FIXME: don't override the existing remote_user, instead create
        # a different member like 'remote_user_profile'.
        req.remote_user = UserProfile.get_by_name(req.envid,
                                                  req.remote_user)
