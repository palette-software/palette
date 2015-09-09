""" Helper classes that exist entirely within the Request lifecycle """
# pylint: enable=missing-docstring,relative-import
from webob import exc

from akiri.framework import GenericWSGI
import akiri.framework.sqlalchemy as meta

from controller.domain import Domain
from controller.environment import Environment
from controller.profile import UserProfile
from controller.system import SystemEntry, SystemKeys, SystemMixin
from controller.system import DEFAULTS, cast, default
from controller.util import translate_key

class System(dict, SystemMixin):
    """ Caching container for all system table entries.  The object is created
    and destroyed with the request instance. """
    # pylint: disable=too-many-public-methods

    def __init__(self, req):
        # pylint: disable=no-member
        super(System, self).__init__()
        # Start with the default values from the JSON file.
        for key in DEFAULTS:
            dict.__setitem__(self, key, default(key))
        # Technically, req doesn't need to be saved, only envid is used,
        # but this reiterates that the system lifecycle is the same as
        # that of the request.
        self.req = req
        self.import_dict(req.envid)

    def __delitem__(self, key):
        """
        Delete a row from the system table.
        NOTE: The database delete is only done if the key is found
        in the data dict.
        """
        dict.__delitem__(self, key)
        SystemEntry.delete(filters={'envid':self.req.envid, 'key':key})

    def __setitem__(self, key, value):
        """ Update the system table but don't do a database commit """

        value = cast(key, value)
        if key in self:
            if value == self[key]: # always string comparison
                return

        session = meta.Session()
        entry = SystemEntry(envid=self.req.envid, key=key, value=value)
        session.merge(entry)
        dict.__setitem__(self, key, value)

    def import_dict(self, envid):
        """ Import the database system table into self (which is dict-like) """
        for entry in SystemEntry.get_all(envid):
            dict.__setitem__(self, entry.key, entry.typed())

    def todict(self, pretty=False):
        """
        Return a copy of the dict(), translating the keys to or
        from pretty if necessary.
        """
        data = {}
        for key in self:
            data[translate_key(key, pretty=pretty)] = self[key]
        return data


class Platform(object):
    """ This class determines the type of system currently running,
    specifically this instance determines Pro versus Enterprise. """

    # FIXME: move to controller.system.types
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
        return self.req.system[SystemKeys.PLATFORM_PRODUCT]

    @property
    def image(self):
        """ The image type: AWS or VMware, default: VMware """
        return self.req.system[SystemKeys.PLATFORM_IMAGE]

    @property
    def location(self):
        """ Where the image is running: Palette AWS or Customer location,
        default: Customer location"""
        return self.req.system[SystemKeys.PLATFORM_LOCATION]

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
