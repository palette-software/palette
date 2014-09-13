from akiri.framework.api import Request as apiRequest

# pylint: disable=import-error,no-name-in-module
from akiri.framework.ext.sqlalchemy import meta
# pylint: enable=import-error,no-name-in-module

from controller.environment import Environment
from controller.profile import UserProfile
from controller.system import SystemEntry
from controller.util import DATEFMT

class Request(apiRequest):
    """ This class may be called more than once in the WSGI Pipeline. """
    # pylint: disable=too-many-public-methods
    def __init__(self, environ):
        super(Request, self).__init__(environ)
        if not 'PALETTE_ENVIRONMENT' in environ:
            environ['PALETTE_ENVIRONMENT'] = Environment.get()
        self.envid = environ['PALETTE_ENVIRONMENT'].envid

        if isinstance(self.remote_user, basestring):
            self.remote_user = UserProfile.get_by_name(self.envid,
                                                       self.remote_user)

        if 'PALETTE_SYSTEM' in self.environ:
            self.system = environ['PALETTE_SYSTEM']
        else:
            self.system = System(self.envid)
            environ['PALETTE_SYSTEM'] = self.system


# FIXME: merge with SystemManager.
class System(object):

    def __init__(self, envid):
        self.envid = envid

    def tryload(self):
        # pylint: disable=attribute-defined-outside-init
        if not hasattr(self, 'data'):
            self.data = {}
            for entry in SystemEntry.get_all(self.envid):
                self.data[entry.key] = entry

    def modification_time(self, key):
        self.tryload()
        if not key in self.data:
            return None
        return self.data[key].modification_time.strftime(DATEFMT)

    def get(self, key, **kwargs):
        if 'default' in kwargs:
            default = kwargs['default']
            have_default = True
            del kwargs['default']
        else:
            have_default = False

        # if one is requested, read in all entries.
        self.tryload()

        if not key in self.data:
            if have_default:
                return default
            raise ValueError('No such value: ' + key)

        entry = self.data[key]
        return entry.value

    def save(self, key, value):
        self.tryload()

        session = meta.Session()
        if key in self.data:
            entry = self.data[key]
        else:
            entry = SystemEntry(envid=self.envid, key=key, value=value)
            session.add(entry)
            self.data[key] = entry
        entry.value = value
        session.commit()
