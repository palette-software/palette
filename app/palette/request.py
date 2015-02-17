from akiri.framework import GenericWSGI
import akiri.framework.sqlalchemy as meta

from controller.domain import Domain
from controller.environment import Environment
from controller.system import SystemEntry
from controller.util import DATEFMT

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

ENVIRON_ENVIRONMENT_NAME = 'palette.environment'
ENVIRON_DOMAIN_NAME = 'palette.domain'

def req_getattr(req, name):
    if name == 'envid':
        return req.palette_environment.envid
    if name == 'palette_environment': # to be consistent with palette_domain
        if not ENVIRON_ENVIRONMENT_NAME in req.environ:
            req.environ[ENVIRON_ENVIRONMENT_NAME] = Environment.get()
        return req.environ[ENVIRON_ENVIRONMENT_NAME]
    if name == 'palette_domain': # webob already has a 'domain' property.
        if not ENVIRON_DOMAIN_NAME in req.environ:
            req.environ[ENVIRON_DOMAIN_NAME] = Domain.getone()
        return req.environ[ENVIRON_DOMAIN_NAME]
    if name == 'system':
        return System(req.envid)

    raise AttributeError(name)


class BaseMiddleware(GenericWSGI):
    """Do initial setup of the request object."""
    def service(self, req):
        req.getattr = req_getattr
        return None

def make_base(app, global_conf):
    # pylint: disable=unused-argument
    return BaseMiddleware(app)
