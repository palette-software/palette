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

    def get(self, name, default=None):
        if not name in self.GET:
            return default
        return self.GET[name]

    def getint(self, name, default=None):
        try:
            return int(self.GET[name])
        except StandardError:
            pass
        return default

    def getfloat(self, name, default=None):
        try:
            return float(self.GET[name])
        except StandardError:
            pass
        return default

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

    def delete(self, key, synchronize_session='evaluate'):
        if hasattr(self, 'data'):
            if key in self.data:
                del self.data[key]
        filters = {'envid':self.envid, 'key':key}
        SystemEntry.delete(filters, synchronize_session=synchronize_session)

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
            raise KeyError('No such key: ' + key)

        entry = self.data[key]
        return entry.value

    def getint(self, key, **kwargs):
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
            value = int(self.get(key))
        except KeyError, ex:
            if have_default:
                return default
            raise ex
        except ValueError, ex:
            if cleanup:
                if 'synchronize_session' in kwargs:
                    synchronize_session = kwargs['synchronize_session']
                else:
                    synchronize_session = 'evaluate'
                self.delete(key, synchronize_session=synchronize_session)
            if have_default:
                return default
            raise ex
        return value

    def save(self, key, value):
        self.tryload()

        session = meta.Session()
        if key in self.data:
            entry = self.data[key]
        else:
            entry = SystemEntry(envid=self.envid, key=key, value=value)
            session.add(entry)
            self.data[key] = entry
        entry.value = str(value)
        session.commit()
